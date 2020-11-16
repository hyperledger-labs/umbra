import os
import json
import logging
import ipaddress
from collections import defaultdict

import iroha

from umbra.design.basis import Topology
from umbra.design.base.iroha.iroha_genesis import genesis_base as iroha_genesis

logger = logging.getLogger(__name__)


class IrohaTopology(Topology):
    def __init__(self, name, clear_dir=True):
        Topology.__init__(self, name, model="iroha")
        self.project_network = "umbra"
        self.network_mode = "umbra"
        self.domain = "umbra"
        self._admin = {}
        self._test = {}
        self._node_keys = 1
        self._genesis = {}
        self._nodes = {}
        self._networks = {}
        self._internal_port = 10001
        self._node_postgres_port = 5432
        self._torii_port = 10101
        self._postgres_command = (
            "docker-entrypoint.sh -c 'max_prepared_transactions=100'"
        )
        self._ip_network = ipaddress.IPv4Network("172.31.0.0/16")
        self._ip_network_assigned = []
        self._format_iroha_admin()
        self._format_iroha_test()
        self._cfgs()
        self.clear_cfgs(clear_dir)

    def set_domain(self, domain):
        self.domain = domain

    def _cfgs(self):
        filename = "iroha.yaml"
        dirname = "./base/iroha"
        self._filepath_fabricbase = self._join_full_path(dirname, filename)

    def defaults(self):
        self._admin = {}
        self._node_keys = 1
        self._genesis = {}
        self._nodes = {}
        self._networks = {}
        self._node_postgres_port = 5432
        self._torii_port = 10101
        self._ip_network = ipaddress.IPv4Network("172.31.0.0/16")
        self._ip_network_assigned = []
        self.clear_cfgs()

    def _format_iroha_admin(self):
        keys = self._format_node_keys()
        admin = {
            "keys": keys,
            "account": "admin@" + self.domain,
        }
        self._admin = admin

    def _format_iroha_test(self):
        keys = self._format_node_keys()
        test = {
            "keys": keys,
            "account": "test@" + self.domain,
        }
        self._test = test

    def clear_cfgs(self, clear_dir=True):
        _tmp_dir = self.get_settings()
        if clear_dir:
            cfgs_folder = self._full_path(_tmp_dir)
            for root, dirs, files in os.walk(cfgs_folder, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))

    def _format_fqdn(self, node_name, domain):
        node_fqdn = node_name + "." + domain
        return node_fqdn

    def _make_dir(self, folder):
        ack = False

        try:
            os.makedirs(folder)
            logger.debug(f"Dir created: {folder}")
        except FileExistsError:
            logger.debug(f"Dir already exists: {folder}")
        except OSError as e:
            logger.debug(f"Dir {folder} creation error: {repr(e)}")
        else:
            ack = True
        finally:
            return ack

    def _make_nodes_configs_dirs(self):
        acks = []
        for node in self._nodes.values():
            node_folder = node.get("folder")
            node_cfgs_folder = self._full_path(node_folder)
            ack = self._make_dir(node_cfgs_folder)
            acks.append(ack)

        all_acks = all(acks)
        return all_acks

    def _make_configs_dirs(self):
        cfgs_folder = self._full_path(self.get_settings())
        self._make_dir(cfgs_folder)

    def _load_base_profile(self, profile_type):
        datafile = self.read_file(self._filepath_fabricbase)
        if datafile:
            if profile_type in datafile:
                profile_template = datafile.get(profile_type)
                return profile_template
        return None

    def _format_node_keys(self):
        priv = iroha.IrohaCrypto.private_key()
        pub = iroha.IrohaCrypto.derive_public_key(priv)
        keys = {"pub": pub.decode("ascii"), "priv": priv.decode("ascii")}
        return keys

    def _peer_format_fields_list(self, info, fields):
        fields_frmt = []
        for field in fields:
            field_filled = field.format(**info)
            fields_frmt.append(field_filled)
        return fields_frmt

    def _format_port_bindings(self, port_bindings):
        port_bindings_dict = dict([tuple(bind.split(":")) for bind in port_bindings])
        port_bindings_dict = {int(k): int(v) for k, v in port_bindings_dict.items()}
        return port_bindings_dict

    def _parse_node_template(self, node):
        node_kwargs = {}
        node_template = self._load_base_profile("node")

        image = node_template.get("image").format(
            **{"image_tag": node.get("image_tag")}
        )
        environment = node_template.get("environment")
        env_vars = self._peer_format_fields_list(
            node, node_template.get("environment_format")
        )
        environment.extend(env_vars)
        volumes = self._peer_format_fields_list(node, node_template.get("volumes"))
        port_bindings = self._peer_format_fields_list(node, node_template.get("ports"))
        command = node_template.get("command")
        command = command.format(**node)

        node_kwargs = {
            "image": image,
            "env": environment,
            "volumes": volumes,
            "port_bindings": self._format_port_bindings(port_bindings),
            "ports": node.get("ports"),
            "working_dir": node_template.get("working_dir", ""),
            "network_mode": self.network_mode,
            "command": command,
            "environment": node.get("environment"),
        }
        return node_kwargs

    def _parse_node_postgres_template(self, node):
        node_kwargs = {}
        node_template = self._load_base_profile("node_postgres")

        image = node_template.get("image").format(
            **{"postgres_image_tag": node.get("postgres_image_tag")}
        )
        environment = node_template.get("environment")
        env_vars = self._peer_format_fields_list(
            node, node_template.get("environment_format")
        )
        environment.extend(env_vars)
        command = node_template.get("command").format(
            **{"postgres_command": node.get("postgres_command")}
        )

        node_kwargs = {
            "image": image,
            "env": environment,
            "volumes": node_template.get("volumes", []),
            "port_bindings": node_template.get("port_bindings", {}),
            "ports": [],
            "working_dir": node_template.get("working_dir", ""),
            "network_mode": self.network_mode,
            "command": command,
            "environment": node.get("environment"),
        }
        return node_kwargs

    def _format_folder(self, node_fqdn):
        base_folder = self.get_settings()
        node_folder = os.path.join(base_folder, node_fqdn)
        return node_folder

    def _check_node_settings(self, settings):
        defaults = {
            "max_proposal_size": 10,
            "proposal_delay": 5000,
            "vote_delay": 5000,
            "mst_enable": False,
            "mst_expiration_time": 1440,
            "max_rounds_delay": 3000,
            "stale_stream_max_rounds": 2,
        }

        if settings and type(settings) is dict:
            for k in defaults:
                v = settings.get(k, None)

                if v:
                    defaults[k] = v

        return defaults

    def _format_node_key(self, name):
        k = str(self._node_keys)
        # node_key = "-".join([name, k])
        node_key = name + k
        return node_key

    def _format_node_postgres(self, name):
        node_postgres = "postgres-" + name
        return node_postgres

    def add_iroha_node(
        self, name, profile, image_tag="latest", postgres_image_tag="9.5", settings=None
    ):
        node_fqdn = self._format_fqdn(name, self.domain)
        node_folder = self._format_folder(node_fqdn)
        node_settings = self._check_node_settings(settings)
        node_key = self._format_node_key(name)
        node_postgres_host = self._format_node_postgres(name)
        node_keys = self._format_node_keys()

        node = {
            "name": name,
            "domain": self.domain,
            "fqdn": node_fqdn,
            "image_tag": image_tag,
            "nodekey": node_key,
            "postgres_image_tag": postgres_image_tag,
            "postgres_command": self._postgres_command,
            "postgres_host": node_postgres_host,
            "postgres_port": self._node_postgres_port,
            "port": self._torii_port,
            "ports": [self._torii_port],
            "internal_port": self._internal_port,
            "folder": node_folder,
            "postgres_user": node_fqdn,
            "postgres_pass": node_fqdn,
            "settings": node_settings,
            "keys": node_keys,
            "profile": profile,
            "intf": 1,
            "ips": {},
            "environment-address": "",
            "environment": "",
            "blockstore_volume": node_fqdn,
        }

        ack = self._nodes.setdefault(name, node)
        ack_name = ack.get("name", None)

        if ack_name == name:
            logger.debug(f"Node added {name}")
            self._node_keys += 1
            self._torii_port += 1

        else:
            logger.debug(f"Node not added {name} - already existent {ack_name}")

    def add_network(self, net, envid=None):
        if not envid:
            env_scenario = self._get_default_env_scenario()
            envid = env_scenario.get("id")

        if envid in self._environments:
            if net not in self._networks:
                self._networks[net] = {
                    "links": {},
                    "environment": envid,
                    "tun_ids": 1,
                }
            else:
                logger.info(f"Network not added - name {net} already existent")
        else:
            logger.info(f"Network not added - env {envid} not existent")

    def add_link_node_network(self, node, network, profile):
        if network in self._networks and node in self._nodes:
            net = self._networks[network]
            net["links"][node] = {
                "profile": profile,
                "type": "internal",
            }

    def add_networks_link(self, src, dst):

        if src in self._networks and dst in self._networks:

            src_net = self._networks[src]
            src_net_env_name = src_net.get("environment")

            dst_net = self._networks[dst]
            dst_net_env_name = dst_net.get("environment")

            logger.debug(
                f"Add network link environments: src {src_net_env_name} - dst {dst_net_env_name}"
            )

            if src_net_env_name == dst_net_env_name:
                link_type = "internal"
                src_net["links"][dst] = {
                    "profile": {},
                    "type": link_type,
                }
            else:
                link_type = "external"

                # Adds forward tunnel

                dst_net_env = self._environments.get(dst_net_env_name)
                dst_net_env_address_ip = dst_net_env.get("host").get("address")

                src_net_tun_id = src_net.get("tun_ids")
                src_tun_id = "tun" + str(src_net_tun_id)
                src_tun_remote_ip = dst_net_env_address_ip

                src_net_env = self._environments.get(src_net_env_name)
                src_net_env_address_ip = src_net_env.get("host").get("address")

                dst_net_tun_id = dst_net.get("tun_ids")
                dst_tun_id = "tun" + str(dst_net_tun_id)
                dst_tun_remote_ip = src_net_env_address_ip

                src_net["links"][dst] = {
                    "type": link_type,
                    "src_tun_id": src_tun_id,
                    "src_tun_remote_ip": src_tun_remote_ip,
                    "dst_tun_id": dst_tun_id,
                    "dst_tun_remote_ip": dst_tun_remote_ip,
                }

                src_net["tun_ids"] = src_net_tun_id + 1
                dst_net["tun_ids"] = dst_net_tun_id + 1

    def get_network_ip(self):
        available_ips = list(self._ip_network.hosts())
        available_index = len(self._ip_network_assigned)
        ip = str(available_ips[available_index]) + "/" + str(self._ip_network.prefixlen)
        self._ip_network_assigned.append(available_ips[available_index])
        return ip

    def _build_network(self):

        for net_name, net in self._networks.items():
            self.add_node(net_name, "switch", None, **net)
            links = net.get("links")

            for link_dst in links:
                link_profile = links[link_dst].get("profile")
                link_type = links[link_dst].get("type")

                if link_type == "internal":

                    if link_dst in self._nodes:
                        node = self._nodes.get(link_dst)
                        node_fqdn = node.get("fqdn")
                        intf = node.get("intf")
                        intf_name = "eth" + str(intf)
                        intf_ip = self.get_network_ip()
                        self.add_link_nodes(
                            node_fqdn,
                            net_name,
                            link_type,
                            link_profile,
                            params_src={
                                "id": intf_name,
                                "interface": "ipv4",
                                "ip": intf_ip,
                            },
                        )
                        node["intf"] += 1
                        node["ips"][intf_name] = intf_ip.split("/")[0]

    def _build_genesis(self):
        test_account = {
            "createAccount": {
                "accountName": "test",
                "domainId": self.domain,
                "publicKey": self._test.get("keys").get("pub"),
            }
        }

        admin_account = {
            "createAccount": {
                "accountName": "admin",
                "domainId": self.domain,
                "publicKey": self._admin.get("keys").get("pub"),
            }
        }
        admin_role = {
            "appendRole": {"accountId": "admin@" + self.domain, "roleName": "admin"}
        }
        admin_creator_role = {
            "appendRole": {"accountId": "admin@" + self.domain, "roleName": "creator"}
        }
        domain = {
            "createDomain": {
                "defaultRole": "user",
                "domainId": self.domain,
            }
        }

        asset = (
            {
                "createAsset": {
                    "assetName": "coin",
                    "domainId": "umbra",
                    "precision": 2,
                }
            },
        )

        transactions_commands = []

        for node in self._nodes.values():
            node_fqdn = node.get("fqdn")
            peer_address = node_fqdn + ":" + str(self._internal_port)
            peer_key = node.get("keys").get("pub")

            peer = {"addPeer": {"peer": {"address": peer_address, "peerKey": peer_key}}}

            transactions_commands.append(peer)

        genesis = {**iroha_genesis}
        logger.debug(f"Iroha genesis base {type(genesis)}: {genesis}")

        commands = genesis["block_v1"]["payload"]["transactions"][0]["payload"][
            "reducedPayload"
        ]["commands"]

        transactions_commands.extend(commands)

        transactions = [
            domain,
            asset,
            admin_account,
            test_account,
            admin_role,
            admin_creator_role,
        ]

        transactions_commands.extend(transactions)

        genesis["block_v1"]["payload"]["transactions"][0]["payload"]["reducedPayload"][
            "commands"
        ] = transactions_commands

        self._genesis = genesis

    def dump(self):
        iroha_cfgs = {
            "genesis": self._genesis,
            "nodes": self._nodes,
            "users": {
                "admin": self._admin,
                "test": self._test,
            },
        }

        info = {
            "iroha": iroha_cfgs,
        }

        self.umbra = info

    def _make_node_settings(self, node):
        settings = self._load_base_profile("node_settings")

        node_settings = node.get("settings")
        settings.update(node_settings)

        node_database = {
            "host": node.get("postgres_host"),
            "port": node.get("postgres_port"),
            "user": node.get("postgres_user"),
            "password": node.get("postgres_pass"),
        }
        settings["database"].update(node_database)
        # pg_opt = settings["pg_opt"]
        # settings["pg_opt"] = pg_opt.format(**node)

        settings["torii_port"] = node.get("port")
        settings["internal_port"] = node.get("internal_port")

        node_folder = node.get("folder")
        node_configfile = self._join_full_path(node_folder, "config.docker")
        self.writefile_json(settings, node_configfile)

    def _save_file(self, filename, folder, data, file_format="json"):
        filepath = self._join_full_path(folder, filename)

        if file_format == "json":
            self.writefile_json(data, filepath)
        elif file_format == "txt":
            self.writefile_txt([data], filepath)
        else:
            logger.debug(
                f"Unknown file format to be saved {file_format} - file {filename} not saved"
            )

    def _make_nodes_configs(self):

        filename_admin_pub_key = "admin@" + self.domain + ".pub"
        filename_admin_priv_key = "admin@" + self.domain + ".priv"
        admin_pub_key = self._admin.get("keys").get("pub")
        admin_priv_key = self._admin.get("keys").get("priv")

        filename_test_pub_key = "test@" + self.domain + ".pub"
        filename_test_priv_key = "test@" + self.domain + ".priv"
        test_pub_key = self._test.get("keys").get("pub")
        test_priv_key = self._test.get("keys").get("priv")

        for node in self._nodes.values():
            self._make_node_settings(node)

            node_folder = node.get("folder")
            self._save_file("genesis.block", node_folder, self._genesis)

            node_key = node.get("nodekey")
            node_keys = node.get("keys")
            filename_pub_key = node_key + ".pub"
            filename_priv_key = node_key + ".priv"
            self._save_file(
                filename_pub_key, node_folder, node_keys.get("pub"), file_format="txt"
            )
            self._save_file(
                filename_priv_key, node_folder, node_keys.get("priv"), file_format="txt"
            )

            self._save_file(
                filename_admin_pub_key, node_folder, admin_pub_key, file_format="txt"
            )
            self._save_file(
                filename_admin_priv_key, node_folder, admin_priv_key, file_format="txt"
            )

            self._save_file(
                filename_test_pub_key, node_folder, test_pub_key, file_format="txt"
            )
            self._save_file(
                filename_test_priv_key, node_folder, test_priv_key, file_format="txt"
            )

    def update_nodes_environment_address(self):
        logger.debug(f"Updating nodes environment address")
        for network in self._networks.values():

            envid = network.get("environment")
            env = self._environments.get(envid)
            env_address = env.get("host").get("address")

            for node_name in network.get("links"):

                if node_name in self._nodes:

                    node = self._nodes.get(node_name, None)
                    node["environment-address"] = env_address
                    node["environment"] = envid

    def build_configs(self):
        self._make_configs_dirs()
        self._make_nodes_configs_dirs()
        self._build_genesis()
        self._make_nodes_configs()

    def _build_network_dns(self):
        dns_names = {}
        dns_nodes = []

        for net in self._networks.values():
            links = net.get("links")
            for node_name in links:
                if node_name in self._nodes:
                    node = self._nodes.get(node_name)

                    node_fqdn = node.get("fqdn")
                    node_ips = node.get("ips")

                    dns_nodes.append(node_fqdn)
                    for ip in node_ips.values():
                        dns_names[node_fqdn] = ip

        for n, data in self.graph.nodes(data=True):
            if n in dns_nodes:
                data["extra_hosts"] = dns_names

    def _build_nodes(self):
        for node in self._nodes.values():
            node_kwargs = self._parse_node_template(node)
            self.add_node(
                node.get("fqdn"),
                "container",
                node.get("profile"),
                **node_kwargs,
            )

            node_postgres_kwargs = self._parse_node_postgres_template(node)
            self.add_node(
                node.get("postgres_host"),
                "container",
                node.get("profile"),
                **node_postgres_kwargs,
            )

    def build(self):
        self.update_nodes_environment_address()
        self.build_configs()
        self._build_nodes()
        self._build_network()
        self._build_network_dns()
        self.dump()
        topo = Topology.build(self)
        return topo
