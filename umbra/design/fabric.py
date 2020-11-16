import os
import logging
import ipaddress
import subprocess
from collections import defaultdict

from umbra.design.basis import Topology


logger = logging.getLogger(__name__)


class FabricTopology(Topology):
    def __init__(self, name, chaincode_dir=None, clear_dir=True):
        Topology.__init__(self, name, model="fabric")
        self.project_network = "umbra"
        self.network_mode = "umbra"
        self.orgs = {}
        self.orderers = {}
        self.agent = {}
        self._config_tx = {}
        self._configtx_fill = {}
        self._networks = {}
        self._ca_ports = 7054
        self._peer_ports = 2000
        self._peer_subports = 51
        self._peer_events_subports = 7053
        self._ip_network = ipaddress.IPv4Network("172.31.0.0/16")
        self._ip_network_assigned = []
        self._filepath_fabricbase = None
        self._configtx_path = None
        self._configsdk_path = None
        self._chaincode_path = chaincode_dir
        self._cfgs()
        self.clear_cfgs(clear_dir)

    def _cfgs(self):
        filename = "fabric.yaml"
        dirname = "./base/fabric/"
        self._filepath_fabricbase = self._join_full_path(dirname, filename)

    def defaults(self):
        self.project_network = "umbra"
        self.network_mode = "umbra"
        self._ca_ports = 7054
        self._peer_ports = 7000
        self._peer_subports = 51
        self.orgs = {}
        self.orderers = {}
        self._config_tx = {}
        self._configtx_fill = {}
        self._networks = {}
        self._environments = {}
        self.clear_cfgs()
        self._ip_network = ipaddress.IPv4Network("172.31.0.0/16")
        self._ip_network_assigned = []

    def clear_cfgs(self, clear_dir=True):
        _tmp_dir = self.get_settings()
        if clear_dir:
            cfgs_folder = self._full_path(_tmp_dir)
            for root, dirs, files in os.walk(cfgs_folder, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))

    def configtx(self, conf):
        self._config_tx = conf

    def add_node_network_link(self, org, node, network, profile):
        if network in self._networks:
            net = self._networks[network]

            if org in self.orgs:
                org_data = self.orgs.get(org)
                org_peers = org_data.get("peers")
                org_CAs = org_data.get("CAs")

                node_fqdn = None
                if node in org_peers:
                    peer = org_peers.get(node)
                    node_fqdn = peer.get("peer_fqdn")

                if node in org_CAs:
                    CA = org_CAs.get(node)
                    node_fqdn = CA.get("ca_fqdn")

                if node_fqdn:
                    net["links"][node_fqdn] = {
                        "profile": profile,
                        "type": "internal",
                        "org": org,
                        "node": node,
                    }

    def add_org_network_link(self, org, network, profile):
        if network in self._networks and org in self.orgs:
            net = self._networks[network]
            net["links"][org] = {
                "profile": profile,
                "type": "internal",
                "org": org,
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

    def add_network(self, net, envid=None):
        if not envid:
            env_scenario = self._get_default_env_scenario()
            envid = env_scenario.get("id")

        if envid in self._environments:
            if net not in self._networks:
                self._networks[net] = {
                    "links": {},
                    "env": envid,
                    "environment": envid,
                    "tun_ids": 1,
                }
            else:
                logger.info(f"Network not added - name {net} already existent")
        else:
            logger.info(f"Network not added - env {envid} not existent")

    def add_org(self, name, domain, EnableNodeOUs=True, policies=None):
        org = {
            "name": name,
            "domain": domain,
            "org_fqdn": name + "." + domain,
            "EnableNodeOUs": EnableNodeOUs,
            "msp_id": name + "MSP",
            "peers": {},
            "CAs": {},
            "policies": policies if policies else {},
            "anchor": None,
        }
        if name not in self.orgs:
            self.orgs[name] = org
            logger.info("Org registered %s", name)
        else:
            logger.info("Org already exists %s", name)

    def add_orderer(
        self,
        name,
        domain,
        profile=None,
        mode="raft",
        specs=None,
        org=None,
        policies=None,
        image_tag="1.4.0",
    ):
        orderer = {
            "name": name,
            "domain": domain,
            "profile": profile,
            "mode": mode,
            "specs": specs,
            "orderer_fqdn": name + "." + domain,
            "port": 7050,  # TODO Hardcoded! get to know how to change it!
            "ports": [7050],
            "org": org,
            "policies": policies if policies else {},
            "msp_id": name + "MSP",
            "image_tag": image_tag,
            "intf": 1,
            "ips": {},
            "environment-address": "",
        }
        if name not in self.orderers:
            orderer["orderer_path"] = self.get_node_dir(orderer, orderer=True)
            orderer["root_config"] = self._full_path(self.get_settings())

            self.orderers[name] = orderer
            logger.info("Orderer registered %s - %s", name, domain)
        else:
            logger.info("Orderer already exists %s", name)

    def add_ca(
        self,
        name,
        org_name,
        domain,
        ca_admin,
        ca_admin_pw,
        profile=None,
        image_tag="1.4.0",
    ):
        CA = {
            "name": name,
            "org": org_name,
            "profile": profile,
            "name_org": name + "-" + org_name,
            "domain": domain,
            "port": self._ca_ports,
            "ports": [self._ca_ports],
            "ca_fqdn": ".".join([name, org_name, domain]),
            "image_tag": image_tag,
            "ca_keyfile": None,
            "ca_admin": ca_admin,
            "ca_admin_pw": ca_admin_pw,
            "intf": 1,
            "ips": {},
            "environment-address": "",
        }
        if org_name in self.orgs:
            org = self.orgs[org_name]
            org_CAs = org.get("CAs")
            org_fqdn = ".".join([org_name, domain])
            CA["org_fqdn"] = org_fqdn

            if name not in org_CAs:
                org_CAs[name] = CA
                logger.info("CA registered %s - %s", name, org_fqdn)
                self._ca_ports += 1

            else:
                logger.info("CA already exists %s", name)
        else:
            logger.info("Org %s for CA %s not registered", org_name, name)

    def add_peer(self, name, org_name, anchor=False, profile=None, image_tag="1.4.0"):
        peer = {
            "name": name,
            "org": org_name,
            "anchor": anchor,
            "profile": profile,
            "port": self._peer_ports + self._peer_subports,
            "ports": [self._peer_ports + self._peer_subports],
            "chaincode_port": self._peer_ports + self._peer_subports + 1,
            "image_tag": image_tag,
            "project_network": self.project_network,
            "peer_anchor_fqdn": None,  # TODO add anchor fqdn when build_configs
            "peer_anchor_port": None,
            "intf": 1,
            "ips": {},
            "environment-address": "",
            "environment": "",
        }

        if org_name in self.orgs:
            org = self.orgs[org_name]
            org_peers = org.get("peers")

            org_fqdn, peer_fqdn = self._format_fqdn(name, org_name)

            if anchor:
                org["anchor"] = name

            peer["peer_msp_id"] = org.get("msp_id")
            peer["org_fqdn"] = org_fqdn
            peer["peer_fqdn"] = peer_fqdn
            peer["peer_path"] = self.get_node_dir(peer)
            peer["root_config"] = self._full_path(self.get_settings())

            if name not in org_peers:
                self._peer_ports += 1000  # Updates port for next peer
                org_peers[name] = peer
                logger.info("Peer registered %s", peer_fqdn)

            else:
                logger.info("Peer already exists %s", name)
        else:
            logger.info("Org %s for peer %s not registered", org_name, name)

    def _format_fqdn(self, peer_name, org_name):
        org = self.orgs.get(org_name)
        domain = org.get("domain")
        org_fqdn = org_name + "." + domain
        peer_fqdn = peer_name + "." + org_fqdn
        return org_fqdn, peer_fqdn

    def _load_base_profile(self, profile_type):
        datafile = self.read_file(self._filepath_fabricbase)
        if datafile:
            if profile_type in datafile:
                profile_template = datafile.get(profile_type)
                return profile_template
        return None

    def _format_port_bindings(self, port_bindings):
        port_bindings_dict = dict([tuple(bind.split(":")) for bind in port_bindings])
        port_bindings_dict = {int(k): int(v) for k, v in port_bindings_dict.items()}
        return port_bindings_dict

    def _parse_orderer_template(self, orderer):
        orderer_kwargs = {}
        orderer_template = self._load_base_profile("orderer-base")

        image = orderer_template.get("image").format(
            **{"image_tag": orderer.get("image_tag")}
        )
        environment = orderer_template.get("environment")
        env_vars = self._peer_format_fields_list(
            orderer, orderer_template.get("environment_format")
        )
        environment.extend(env_vars)
        volumes = self._peer_format_fields_list(
            orderer, orderer_template.get("volumes")
        )
        port_bindings = self._peer_format_fields_list(
            orderer, orderer_template.get("ports")
        )

        orderer_kwargs = {
            "image": image,
            "env": environment,
            "volumes": volumes,
            "port_bindings": self._format_port_bindings(port_bindings),
            "ports": orderer.get("ports"),
            "working_dir": orderer_template.get("working_dir"),
            "network_mode": self.network_mode,
            "command": orderer_template.get("command"),
        }
        return orderer_kwargs

    def _build_orderers(self):
        for orderer in self.orderers.values():
            orderer_kwargs = self._parse_orderer_template(orderer)
            self.add_node(
                orderer.get("orderer_fqdn"),
                "container",
                orderer.get("profile"),
                **orderer_kwargs,
            )

    def _build_agent(self):
        for agent in self.agent.values():
            agent_kwargs = {
                "image": agent.get("image") + ":" + agent.get("image_tag"),
                "env": agent.get("environment"),
                "volumes": [],
                "port_bindings": {},
                "ports": agent.get("ports"),
                "working_dir": "",
                "network_mode": self.network_mode,
                "command": "",
            }
            self.add_node(agent.get("agent_fqdn"), "container", **agent_kwargs)

    def _peer_format_fields_list(self, info, fields):
        fields_frmt = []
        for field in fields:
            field_filled = field.format(**info)
            fields_frmt.append(field_filled)
        return fields_frmt

    def _parse_node_template(self, node, template):
        node_kwargs = {}
        node_template = self._load_base_profile(template)

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

        if template == "ca-base":
            command = command.format(**node)

        node_kwargs = {
            "image": image,
            "env": environment,
            "volumes": volumes,
            "port_bindings": self._format_port_bindings(port_bindings),
            "ports": node.get("ports"),
            "working_dir": node_template.get("working_dir"),
            "network_mode": self.network_mode,
            "command": command,
            "environment": node.get("environment"),
        }
        return node_kwargs

    def _build_peers(self):
        for org in self.orgs.values():
            orgs_peers = org.get("peers")
            for peer in orgs_peers.values():
                peer_kwargs = self._parse_node_template(peer, "peer-base")
                self.add_node(
                    peer.get("peer_fqdn"),
                    "container",
                    peer.get("profile"),
                    **peer_kwargs,
                )

    def _build_CAs(self):
        for org in self.orgs.values():
            orgs_CAs = org.get("CAs")
            for CA in orgs_CAs.values():
                CA_kwargs = self._parse_node_template(CA, "ca-base")
                self.add_node(
                    CA.get("ca_fqdn"), "container", CA.get("profile"), **CA_kwargs
                )

    def get_network_ip(self):
        available_ips = list(self._ip_network.hosts())
        available_index = len(self._ip_network_assigned)
        ip = str(available_ips[available_index]) + "/" + str(self._ip_network.prefixlen)
        self._ip_network_assigned.append(available_ips[available_index])
        return ip

    def _fill_org_anchors(self):
        for org in self.orgs.values():
            org_peers = org.get("peers")
            peer_anchor_name = org.get("anchor")

            peer_anchor = org_peers.get(peer_anchor_name)
            if not peer_anchor:
                peer_anchor = org_peers.values()[0]

            peer_anchor_fqdn = peer_anchor.get("peer_fqdn")
            peer_anchor_port = peer_anchor.get("port")

            for peer in org_peers.values():
                peer["peer_anchor_fqdn"] = peer_anchor_fqdn
                peer["peer_anchor_port"] = peer_anchor_port

    def _build_network(self):
        # TODO: check links and set switches stp if needed (remember wait time - convergence)
        # e.g., https://gist.github.com/lantz/7853026

        for net_name, net in self._networks.items():
            self.add_node(net_name, "switch", None, **net)
            links = net.get("links")

            for link_dst in links:
                link_profile = links[link_dst].get("profile")
                link_type = links[link_dst].get("type")

                if link_type == "internal":

                    if link_dst in self.orgs:
                        org = self.orgs[link_dst]
                        org_CAs = org.get("CAs")
                        org_peers = org.get("peers")

                        # logger.debug("Add links for net - org - peers - CAs", net_name, link_dst, org_peers.keys(), org_CAs.keys())

                        for peer in org_peers.values():
                            peer_fqdn = peer.get("peer_fqdn")
                            intf = peer.get("intf")
                            intf_name = "eth" + str(intf)
                            intf_ip = self.get_network_ip()
                            self.add_link_nodes(
                                peer_fqdn,
                                net_name,
                                link_type,
                                link_profile,
                                params_src={
                                    "id": intf_name,
                                    "interface": "ipv4",
                                    "ip": intf_ip,
                                },
                            )  # TODO verify params_src (intf and ipv4)
                            peer["intf"] += 1
                            peer["ips"][intf_name] = intf_ip.split("/")[0]

                        for CA in org_CAs.values():
                            ca_fqdn = CA.get("ca_fqdn")
                            intf = CA.get("intf")
                            intf_name = "eth" + str(intf)
                            intf_ip = self.get_network_ip()
                            self.add_link_nodes(
                                ca_fqdn,
                                net_name,
                                link_type,
                                link_profile,
                                params_src={
                                    "id": intf_name,
                                    "interface": "ipv4",
                                    "ip": intf_ip,
                                },
                            )  # TODO verify params_src (intf and ipv4)
                            CA["intf"] += 1
                            CA["ips"][intf_name] = intf_ip.split("/")[0]

                    elif link_dst in self.orderers:
                        orderer = self.orderers[link_dst]
                        orderer_fqdn = orderer.get("orderer_fqdn")
                        intf = orderer.get("intf")
                        intf_name = "eth" + str(intf)
                        intf_ip = self.get_network_ip()
                        self.add_link_nodes(
                            orderer_fqdn,
                            net_name,
                            link_type,
                            link_profile,
                            params_src={
                                "id": intf_name,
                                "interface": "ipv4",
                                "ip": intf_ip,
                            },
                        )  # TODO verify params_src (intf and ipv4)

                        orderer["intf"] += 1
                        orderer["ips"][intf_name] = intf_ip.split("/")[0]

                    elif link_dst in self._networks:
                        self.add_link_nodes(link_dst, net_name, link_type, link_profile)

                    else:
                        link_org = links[link_dst].get("org", None)
                        link_org_node = links[link_dst].get("node", None)

                        if link_org and link_org_node and link_org in self.orgs:
                            org_data = self.orgs.get(link_org)
                            org_peers = org_data.get("peers")
                            org_CAs = org_data.get("CAs")

                            if link_org_node in org_peers:
                                peer = org_peers.get(link_org_node)
                                peer_fqdn = peer.get("peer_fqdn")
                                intf = peer.get("intf")
                                intf_name = "eth" + str(intf)
                                intf_ip = self.get_network_ip()
                                self.add_link_nodes(
                                    peer_fqdn,
                                    net_name,
                                    link_type,
                                    link_profile,
                                    params_src={
                                        "id": intf_name,
                                        "interface": "ipv4",
                                        "ip": intf_ip,
                                    },
                                )  # TODO verify params_src (intf and ipv4)
                                peer["intf"] += 1
                                peer["ips"][intf_name] = intf_ip.split("/")[0]

                            if link_org_node in org_CAs:
                                CA = org_CAs.get(link_org_node)
                                ca_fqdn = CA.get("ca_fqdn")
                                intf = CA.get("intf")
                                intf_name = "eth" + str(intf)
                                intf_ip = self.get_network_ip()
                                self.add_link_nodes(
                                    ca_fqdn,
                                    net_name,
                                    link_type,
                                    link_profile,
                                    params_src={
                                        "id": intf_name,
                                        "interface": "ipv4",
                                        "ip": intf_ip,
                                    },
                                )  # TODO verify params_src (intf and ipv4)
                                CA["intf"] += 1
                                CA["ips"][intf_name] = intf_ip.split("/")[0]

                if link_type == "external":
                    self.add_link_nodes(
                        net_name,
                        link_dst,
                        link_type,
                        link_profile,
                        params_src={
                            "tun_id": links[link_dst].get("src_tun_id"),
                            "tun_remote_ip": links[link_dst].get("src_tun_remote_ip"),
                        },
                        params_dst={
                            "tun_id": links[link_dst].get("dst_tun_id"),
                            "tun_remote_ip": links[link_dst].get("dst_tun_remote_ip"),
                        },
                    )

    def _build_network_dns(self):
        dns_names = {}
        dns_nodes = []

        for net_name, net in self._networks.items():
            links = net.get("links")
            for org_name in links:
                if org_name in self.orgs:
                    org = self.orgs[org_name]
                    org_CAs = org.get("CAs")
                    org_peers = org.get("peers")

                    for peer in org_peers.values():
                        peer_fqdn = peer.get("peer_fqdn")
                        peer_ips = peer.get("ips")

                        dns_nodes.append(peer_fqdn)
                        for ip in peer_ips.values():
                            dns_names[peer_fqdn] = ip

                    for CA in org_CAs.values():
                        ca_fqdn = CA.get("ca_fqdn")
                        ca_ips = CA.get("ips")

                        dns_nodes.append(ca_fqdn)
                        for ip in ca_ips.values():
                            dns_names[ca_fqdn] = ip

                if org_name in self.orderers:
                    orderer = self.orderers[org_name]
                    orderer_fqdn = orderer.get("orderer_fqdn")
                    orderer_ips = orderer.get("ips")

                    dns_nodes.append(orderer_fqdn)
                    for ip in orderer_ips.values():
                        dns_names[orderer_fqdn] = ip

                if org_name in self.agent:
                    agent = self.agent[org_name]
                    agent_fqdn = agent.get("agent_fqdn")
                    agent_ips = agent.get("ips")
                    dns_nodes.append(agent_fqdn)

                    for ip in agent_ips.values():
                        dns_names[agent_fqdn] = ip

        for n, data in self.graph.nodes(data=True):
            if n in dns_nodes:
                data["extra_hosts"] = dns_names

    def dump(self):
        fabric_cfgs = {
            "configtx": self._configtx_path,
            "configsdk": self._configsdk_path,
            "chaincode": self._chaincode_path,
            "settings": {
                "orgs": self.orgs,
                "orderers": self.orderers,
            },
        }

        info = {
            "fabric": fabric_cfgs,
        }

        self.umbra = info

    def update_nodes_environment_address(self):
        logger.debug(f"Updating nodes environment address")
        for network in self._networks.values():

            envid = network.get("environment")
            env = self._environments.get(envid)
            env_address = env.get("host").get("address")

            for org_name in network.get("links"):

                if org_name in self.orgs:

                    org = self.orgs.get(org_name, None)

                    org_CAs = org.get("CAs", {})
                    org_peers = org.get("peers", {})

                    for peer in org_peers.values():
                        peer["environment-address"] = env_address
                        peer["environment"] = envid

                    for CA in org_CAs.values():
                        CA["environment-address"] = env_address
                        CA["environment"] = envid

                if org_name in self.orderers:
                    orderer = self.orderers.get(org_name, None)
                    orderer["environment-address"] = env_address
                    orderer["environment"] = envid

    def build(self):
        self.update_nodes_environment_address()
        self.build_configs()
        self._build_peers()
        self._build_CAs()
        self._build_orderers()
        self._build_agent()
        self._build_network()
        self._build_network_dns()
        self.dump()
        # topo_envs = Topology.build_environments(self)
        topo = Topology.build(self)
        # self.dump(topo_built, topo_envs)
        return topo

    def loading(self, root, file, full_path):
        files = []
        p = os.path.join(root, file)
        if full_path:
            file_path = os.path.abspath(p)
            files.append(file_path)
        else:
            files.append(file)
        return files

    def get_filepath(self, folder, endswith=None, full_path=False):
        for root, dirs, files in os.walk(folder):
            for file in files:
                # if file.startswith(file_begin_with):
                if endswith:
                    if file.endswith(endswith):
                        file_path = self.loading(root, file, full_path)
                        return file_path
                else:
                    file_path = self.loading(root, file, full_path)
                    return file_path
        return None

    def _fill_node_configs(self):
        for org in self.orgs.values():
            org_CAs = org.get("CAs")
            if org_CAs:
                root_path = self._full_path(self.get_settings())
                org_fqdn = org.get("org_fqdn")
                org_ca_dir = os.path.join(
                    root_path, "peerOrganizations", org_fqdn, "ca"
                )
                ca_keyfile = self.get_filepath(
                    org_ca_dir, endswith="_sk", full_path=False
                )
                for org_CA in org_CAs.values():
                    org_CA["ca_keyfile"] = ca_keyfile.pop()
                    # print("ca_keyfile", org_CA["ca_keyfile"] )
                org_path = self.get_org_dir(org)
                org_CA["org_path"] = org_path

    def _make_configs_dirs(self):
        cfgs_folder = self._full_path(self.get_settings())
        try:
            os.makedirs(cfgs_folder)
            logger.debug(f"Configs dir created: {cfgs_folder}")
        except FileExistsError:
            logger.debug(f"Configs dir already exists: {cfgs_folder}")
        except OSError as e:
            logger.debug(f"Configs dir {cfgs_folder} creation error: {repr(e)}")

    def build_configs(self):
        self._make_configs_dirs()
        self._fill_org_anchors()
        self._build_crypto_config()
        self._build_configtx()
        self._build_config_sdk()
        self._fill_node_configs()

    def get_peers(self, org):
        org_peers = org.get("peers")
        num_peers = len(org_peers.values())
        return num_peers

    def _call(self, args):
        return_code = 0
        out, err = "", None
        try:
            p = subprocess.Popen(
                args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.process = p
            logger.debug("process started %s", p.pid)
            out, err = p.communicate()
            return_code = p.returncode
        except OSError:
            return_code = -1
            err = "ERROR: exception OSError"
        finally:
            if return_code != 0:
                answer = err
            else:
                answer = out
            self.process = None
            logger.debug("Return code %s - output %s", return_code, answer)
            return return_code, answer

    def _build_crypto_config(self):
        crypto_config = {"OrdererOrgs": [], "PeerOrgs": []}

        for org in self.orgs.values():
            num_org_peers = self.get_peers(org)

            org_frmt = {
                "Name": org.get("name"),
                "Domain": org.get("name") + "." + org.get("domain"),
                "EnableNodeOUs": org.get("EnableNodeOUs"),
                "Template": {
                    "Count": num_org_peers,  # TODO: assign peer names accordingly
                    "SANS": ["localhost"],
                },
                "Users": {
                    "Count": 1,
                },
            }

            crypto_config["PeerOrgs"].append(org_frmt)

        for orderer in self.orderers.values():
            ord_frmt = {
                "Name": orderer.get("name"),
                "Domain": orderer.get("domain"),
                "Specs": orderer.get("specs") if orderer.get("specs") else [],
            }
            crypto_config["OrdererOrgs"].append(ord_frmt)

        filename = "crypto-config.yaml"
        filepath = self._join_full_path(self.get_settings(), filename)
        output_path = self._full_path(self.get_settings())

        logger.info("Saving Fabric crypto config file %s", filepath)
        self.write_file(crypto_config, filepath)

        cmd = [self._join_full_path("../../deps/fabric/", "cryptogen")]
        args = ["generate", "--config", filepath, "--output", output_path]
        cmd.extend(args)
        logger.info(
            "Generating  crypto-config.yaml folder structure - calling cryptogen"
        )
        logger.debug("Calling %s", cmd)
        self._call(cmd)

    def get_node_dir(self, node, orderer=False):
        _tmp_dir = self.get_settings()
        root_path = self._full_path(_tmp_dir)

        if orderer:
            org_type = "ordererOrganizations"
            org_fqdn = node.get("domain")
            peer_fqdn = node.get("name") + "." + org_fqdn
            node_dir = os.path.join(
                root_path, org_type, org_fqdn, "orderers", peer_fqdn
            )
        else:
            org_name = node.get("org")
            org_type = "peerOrganizations"
            org_fqdn, peer_fqdn = self._format_fqdn(node.get("name"), org_name)
            node_dir = os.path.join(root_path, org_type, org_fqdn, "peers", peer_fqdn)
        return node_dir

    def get_msp_dir(self, org, orderer=False):
        root_path = self._full_path(self.get_settings())
        if orderer:
            org_type = "ordererOrganizations"
            org_fqdn = org.get("domain")
        else:
            org_type = "peerOrganizations"
            org_fqdn = org.get("name") + "." + org.get("domain")
        org_msp_dir = os.path.join(root_path, org_type, org_fqdn, "msp")
        return org_msp_dir

    def get_org_dir(self, org, orderer=False):
        root_path = self._full_path(self.get_settings())
        if orderer:
            org_type = "ordererOrganizations"
            org_fqdn = org.get("domain")
            org_dir = os.path.join(root_path, org_type, org_fqdn)
        else:
            org_type = "peerOrganizations"
            org_fqdn = org.get("name") + "." + org.get("domain")
            org_dir = os.path.join(root_path, org_type, org_fqdn)
        return org_dir

    def get_path(self, data, path):
        fields = path.split(".")
        fields.reverse()
        datapath = data
        while fields:
            f = fields.pop()
            datapath = datapath.get(f)
        return datapath

    def _frmt_configtx_profiles(self, orgs):
        profiles = self._config_tx.get("Profiles")
        for path, value in self._configtx_fill.items():
            datapath = self.get_path(profiles, path)
            org_names = value.get("fields")
            for org_name in org_names:
                org = orgs.get(org_name)
                datapath.remove(org_name)
                datapath.append(org)

    def set_configtx_profile(self, path, fields):
        self._configtx_fill[path] = {
            "fields": fields,
        }

    def _build_configtx(self):
        orgs_frmt = {}

        for org in self.orgs.values():
            anchors = []
            anchor = org.get("anchor")
            if anchor:
                org_peers = org.get("peers")
                peer = org_peers.get(anchor)
                _, peer_fqdn = self._format_fqdn(anchor, org.get("name"))
                anchor_info = {"Host": peer_fqdn, "Port": peer.get("port")}
                anchors = [anchor_info]

            org_frmt = {
                "Name": org.get("name") + "MSP",
                "ID": org.get("name") + "MSP",
                "MSPDir": self.get_msp_dir(org),
                "Policies": org.get("policies"),
                "AnchorPeers": anchors,
            }
            orgs_frmt[org.get("name")] = org_frmt
            self._config_tx["Organizations"].append(org_frmt)

        for order in self.orderers.values():
            org_frmt = {
                "Name": order.get("name") + "Org",
                "ID": order.get("name") + "MSP",
                "MSPDir": self.get_msp_dir(order, orderer=True),
                "Policies": order.get("policies"),
            }
            orgs_frmt[order.get("name")] = org_frmt
            self._config_tx["Organizations"].append(org_frmt)

        self._frmt_configtx_profiles(orgs_frmt)

        filename = "configtx.yaml"
        filepath = self._join_full_path(self.get_settings(), filename)
        output_path = self._full_path(self.get_settings())

        logger.info("Saving Fabric configtx file %s", filepath)
        self.write_file(self._config_tx, filepath)
        self._configtx_path = output_path

        cmd = self._join_full_path("../../deps/fabric/", "configtxgen")
        logger.info("Generating  configtx.yaml files - calling configtxgen")

        # TODO generate genesis args according to orderer choosen
        genesis_args = [
            "-configPath",
            output_path,
            "-profile",
            "TwoOrgsOrdererGenesis",
            "-channelID",
            "system-channel",
            "-outputBlock",
            output_path + "/genesis.block",
        ]

        channel_args = [
            "-configPath",
            output_path,
            "-profile",
            "TwoOrgsChannel",
            "-channelID",
            "testchannel",
            "-outputCreateChannelTx",
            output_path + "/channel.tx",
        ]

        # TODO generate anchor args according to anchor peers in orgs
        anchor_args1 = [
            "-configPath",
            output_path,
            "-profile",
            "TwoOrgsChannel",
            "-channelID",
            "testchannel",
            "-outputAnchorPeersUpdate",
            output_path + "/Org2MSPanchors.tx",
            "-asOrg",
            "org2MSP",
        ]

        anchor_args2 = [
            "-configPath",
            output_path,
            "-profile",
            "TwoOrgsChannel",
            "-channelID",
            "testchannel",
            "-outputAnchorPeersUpdate",
            output_path + "/Org1MSPanchors.tx",
            "-asOrg",
            "org1MSP",
        ]

        self._build_configtx_call(cmd, genesis_args)
        self._build_configtx_call(cmd, channel_args)
        self._build_configtx_call(cmd, anchor_args1)
        self._build_configtx_call(cmd, anchor_args2)

    def _build_configtx_call(self, cmd, args):
        cmd_list = []
        cmd_list.append(cmd)
        cmd_list.extend(args)
        logger.debug("Calling %s", cmd_list)
        self._call(cmd_list)

    def _get_org_users(self, org, is_orderer=False):
        org_dir = self.get_org_dir(org, orderer=is_orderer)

        org_users_dir = os.path.join(org_dir, "users")

        users_info = {}

        for root, dirs, files in os.walk(org_users_dir):
            for user_dir in dirs:
                org_user = user_dir.split("@")[0]
                org_user_cert_name = user_dir + "-cert.pem"

                org_user_keystore_path = os.path.join(
                    org_users_dir, user_dir, "msp", "keystore"
                )
                org_user_keystore = self.get_filepath(
                    org_user_keystore_path, endswith="_sk", full_path=True
                )

                users_info[org_user] = {
                    "cert": os.path.join(
                        org_users_dir, user_dir, "msp/signcerts/", org_user_cert_name
                    ),
                    "private_key": org_user_keystore.pop(),
                }
            break

        return users_info

    def _build_config_sdk(self):
        config = {
            "name": "sample-network",
            "description": "Sample network for Python SDK testing",
            "version": "0.1",
            "client": {
                "organization": "org1",
                "credentialStore": {
                    "path": "/tmp/hfc-kvs",
                    "cryptoStore": {"path": "/tmp/hfc-cvs"},
                    "wallet": "wallet-name",
                },
            },
        }

        organizations = {}
        for org in self.orgs.values():
            org_peers = org.get("peers")
            org_CAs = org.get("CAs")

            peers_fqdn = [peer.get("peer_fqdn") for peer in org_peers.values()]
            ca_names = [CA.get("name_org") for CA in org_CAs.values()]
            org_users = self._get_org_users(org)

            org_frmt = {
                org.get("org_fqdn"): {
                    "mspid": org.get("msp_id"),
                    "peers": peers_fqdn,
                    "certificateAuthorities": ca_names,
                    "users": org_users,
                }
            }
            organizations.update(org_frmt)

        orderers = {}

        for orderer in self.orderers.values():

            orderers_fqdn = [orderer.get("orderer_fqdn")]
            org_users = self._get_org_users(orderer, is_orderer=True)

            org_frmt = {
                orderer.get("orderer_fqdn"): {
                    "mspid": orderer.get("msp_id"),
                    "orderers": orderers_fqdn,
                    "certificateAuthorities": [],
                    "users": org_users,
                }
            }
            organizations.update(org_frmt)

            orderer_dir = self.get_org_dir(orderer, orderer=True)

            orderer_tls_dir = os.path.join(orderer_dir, "tlsca/")

            orderer_tls_file = self.get_filepath(
                orderer_tls_dir, endswith=".pem", full_path=True
            )

            orderer_frmt = {
                orderer.get("orderer_fqdn"): {
                    "url": orderer.get("environment-address")
                    + ":"
                    + str(orderer.get("port")),
                    "grpcOptions": {
                        "grpc.ssl_target_name_override": orderer.get("orderer_fqdn"),
                        "grpc-max-send-message-length": 15,
                    },
                    "tlsCACerts": {
                        "path": orderer_tls_file.pop(),
                    },
                }
            }

            orderers.update(orderer_frmt)

        config["organizations"] = organizations
        config["orderers"] = orderers

        peers = {}
        CAs = {}
        for org in self.orgs.values():
            org_peers = org.get("peers")
            org_CAs = org.get("CAs")

            for peer in org_peers.values():
                peer_dir = self.get_node_dir(peer)
                peer_tls_dir = os.path.join(peer_dir, "msp/tlscacerts/")
                peer_tls_file = self.get_filepath(
                    peer_tls_dir, endswith=".pem", full_path=True
                )

                peer_frmt = {
                    peer.get("peer_fqdn"): {
                        "url": peer.get("environment-address")
                        + ":"
                        + str(peer.get("port")),
                        "eventUrl": peer.get("environment-address")
                        + ":"
                        + "9053",  # TODO find peer eventurl (set this ENV in fabric.yaml peer-base)
                        "grpcOptions": {
                            "grpc.ssl_target_name_override": peer.get("peer_fqdn"),
                            "grpc.http2.keepalive_time": 15,
                        },
                        "tlsCACerts": {
                            "path": peer_tls_file.pop(),
                        },
                    }
                }
                peers.update(peer_frmt)

            for CA in org_CAs.values():
                org_dir = self.get_org_dir(org)
                org_ca_tls_dir = os.path.join(org_dir, "ca")
                org_ca_tls_file = self.get_filepath(
                    org_ca_tls_dir, endswith=".pem", full_path=True
                )

                CA_frmt = {
                    CA.get("name_org"): {
                        "url": CA.get("environment-address")
                        + ":"
                        + str(CA.get("port")),
                        "grpcOptions": {
                            "verify": True,
                        },
                        "tlsCACerts": {
                            "path": org_ca_tls_file.pop(),
                        },
                        "registrar": [
                            {
                                "enrollId": CA.get("ca_admin"),
                                "enrollSecret": CA.get("ca_admin_pw"),
                            },
                        ],
                    }
                }
                CAs.update(CA_frmt)

        config["certificateAuthorities"] = CAs
        config["peers"] = peers

        filename = "fabric_sdk_config.json"
        filepath = self._join_full_path(self.get_settings(), filename)
        logger.info("Saving Fabric SDK config file %s", filepath)
        self.writefile_json(config, filepath)
        self._configsdk_path = filepath
