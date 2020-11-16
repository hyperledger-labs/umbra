import os
import subprocess
import logging
import json
import yaml
import networkx as nx
import ipaddress
from networkx.readwrite import json_graph
from yaml import load, dump
from collections import defaultdict

logger = logging.getLogger(__name__)


NODES = 10
DEGREE = 5
EDGES_PROB = 0.5
NEIGHBOUR_EDGES = 5
TOPOLOGIES_FOLDER = "./topos/"
BASE_TOPOLOGIES_FOLDER = "./topos/base/"

# port that umbra-agent binds
AGENT_PORT = 8910


class Graph:
    def __init__(self):
        self.graph = nx.MultiGraph()
        self.nodes = NODES
        self.degree = DEGREE
        self.edge_prob = EDGES_PROB
        self.neighbour_edges = NEIGHBOUR_EDGES
        self.folder = TOPOLOGIES_FOLDER
        self.base_folder = BASE_TOPOLOGIES_FOLDER

    def create_graph(self):
        self.graph = nx.MultiGraph()

    def create_random(self, model, kwargs):
        if model == 1:
            degree = kwargs.get("degree", self.degree)
            nodes = kwargs.get("nodes", self.nodes)
            self.graph = nx.random_regular_graph(degree, nodes)
        elif model == 2:
            nodes = kwargs.get("nodes", self.nodes)
            edge_prob = kwargs.get("edge_prob", self.edge_prob)
            self.graph = nx.binomial_graph(nodes, edge_prob)
        elif model == 3:
            nodes = kwargs.get("nodes", self.nodes)
            neighbour_edges = kwargs.get("neighbour_edges", self.neighbour_edges)
            edge_prob = kwargs.get("edge_prob", self.edge_prob)
            self.graph = nx.powerlaw_cluster_graph(nodes, neighbour_edges, edge_prob)
        elif model == 4:
            self.graph = nx.scale_free_graph(self.nodes)
        else:
            nodes = kwargs.get("nodes", self.nodes)
            neighbour_edges = kwargs.get("neighbour_edges", self.neighbour_edges)
            self.graph = nx.barabasi_albert_graph(nodes, neighbour_edges)
        return self.graph

    def parse_filename(self, filename, base=False):
        if base:
            filen = self.base_folder + filename + ".json"
        else:
            filen = self.folder + filename + ".json"
        return filen

    def readfile_json(self, filename, base):
        filename = self.parse_filename(filename, base=base)
        with open(filename, "r") as infile:
            data = json.load(infile)
            return data

    def writefile_json(self, data, filename):
        with open(filename, "w") as outfile:
            json.dump(data, outfile, indent=4, sort_keys=True)
            return True

    def readfile_txt(self, filename, base):
        filename = self.parse_filename(filename, base=base)
        with open(filename, "r") as infile:
            data = infile.readlines()
            return data

    def writefile_txt(self, data, filename):
        with open(filename, "w") as outfile:
            outfile.writelines(data)
            return True

    def save_graph(self, graph, filename, parse_filename=True, base=False):
        if parse_filename:
            filename = self.parse_filename(filename, base=base)
        data = json_graph.node_link_data(graph)
        if self.writefile_json(data, filename):
            return True
        return False

    def retrieve_graph(self, filename, base=False):
        data = self.readfile_json(filename, base=base)
        graph = json_graph.node_link_graph(data)
        return graph

    def parse(self, data):
        self.create_graph()
        nodes = data.get("nodes", {})
        links = data.get("links", {})

        for node in nodes.values():
            node_name = node.get("name")
            if node_name:
                self.graph.add_node(node_name, **node)

        for link in links.values():
            src, dst = link.get("src", None), link.get("dst", None)
            if src and dst:
                self.graph.add_edge(src, dst, **link)

    def shortest_path(self, src, dst):
        path = nx.shortest_path(self.graph, source=src, target=dst)
        return path


class Profile:
    def __init__(self, profile_name):
        self.name = profile_name
        self.node_ids = 1
        self.link_ids = 5000
        self.nodes = {}
        self.links = {}

    def load(self, data):
        self.nodes = data.get("nodes", {})
        self.links = data.get("links", {})

    def dump(self):
        profile = {
            "nodes": self.nodes,
            "links": self.links,
        }
        return profile

    def build_node_resources(self, cpus, memory, disk):
        resources = {
            "cpus": cpus,
            "memory": memory,
            "disk": disk,
        }
        return resources

    def build_link_resources(self, bw, delay, loss):
        resources = {
            "bw": bw,
            "delay": delay,
            "loss": loss,
        }
        return resources

    def add_node(self, node_resources, node_type, node_name=None):
        node_id = self.node_ids
        self.node_ids += 1
        node = {
            "id": node_id,
            "profile": node_type,
            "name": node_name,
            "resources": node_resources,
        }
        self.nodes[node_id] = node
        return node

    def add_link(self, link_resources, link_type):
        link_id = self.link_ids
        self.link_ids += 1
        link = {
            "id": link_id,
            "profile": link_type,
            "resources": link_resources,
        }
        self.links[link_id] = link
        return link

    def get_node(self, node):
        node_profile = node.get("profile")
        resources = self.look_for(node_profile, where="nodes")
        profile = {"resources": resources}
        return profile

    def get_link(self, link):
        link_profile = link.get("profile")
        resources = self.look_for(link_profile, where="links")
        profile = {"resources": resources}
        return profile

    def look_for(self, _type, where):
        if where == "nodes":
            itemset = self.nodes.items()
        elif where == "links":
            itemset = self.links.items()
        else:
            logger.debug("Could not look for profile where %s", where)
            return {}
        types = [(k, v) for (k, v) in itemset if v["profile"] == _type]
        if types:
            (k, v) = types.pop()
            resources = v["resources"]
            return resources
        else:
            logger.debug("Could not look for profile where %s type %s", where, _type)
            return {}


class Lifecycle:
    def __init__(self, name):
        self.name = name
        self.node_ids = 1
        self.link_ids = 5000
        self.nodes = {}
        self.links = {}

    def build_node_workflow(self, name, parameters, method, implementation):
        workflow = {
            "workflow": name,
            "parameters": parameters,
            "method": method,
            "implementation": implementation,
        }
        return workflow

    def add_node(self, workflows, node_name, node_type=None):
        node_id = self.node_ids
        self.node_ids += 1
        node = {
            "id": node_id,
            "type": node_type,
            "name": node_name,
            "workflows": workflows,
        }
        self.nodes[node_id] = node
        return node

    def get_node(self, node):
        node_name = node.get("name")
        workflows = self.look_for(node_name, where="nodes")
        lifecycle = {"lifecycle": workflows}
        return lifecycle

    def look_for(self, name, where):
        if where == "nodes":
            itemset = self.nodes.items()
        else:
            # logger.warning("Could not look for workflows where %s", where)
            return None
        types = [(k, v) for (k, v) in itemset if v["name"] == name]
        if types:
            (k, v) = types.pop()
            workflows = v["workflows"]
            return workflows
        else:
            # logger.error("Could not look for workflows where %s name %s", where, name)
            return None

    def load(self, data):
        self.nodes = data.get("nodes", {})
        self.links = data.get("links", {})

    def dump(self):
        lifecycle = {
            "nodes": self.nodes,
            "links": self.links,
        }
        return lifecycle


class Topology(Graph):
    def __init__(self, name, model, profile_name=None):
        Graph.__init__(self)
        self.name = name
        self.model = model
        self.model_settings = f"/tmp/umbra/{self.model}"
        self.settings = f"/tmp/umbra/{self.model}/{self.name}"
        self.topo = None
        self.umbra = {}
        self.profile = None
        self.profile = Profile(profile_name)
        self.lifecycle = Lifecycle(name)
        self._environments = {}
        self._default_environments()

    def set_default_environment(self, environment):
        keys = ["id", "remote", "components"]
        has_all_keys = all([True if k in environment else False for k in keys])
        if has_all_keys:

            # mandatory_components = ["scenario", "broker"]
            mandatory_components = ["broker"]
            components = environment.get("components")
            has_all_mandatory_components = all(
                [True if k in components else False for k in mandatory_components]
            )
            if has_all_mandatory_components:
                environment["id"] = "umbra-default"
                self._environments["umbra-default"] = environment
                return True

        return False

    def _default_environments(self):
        env_default = {
            "id": "umbra-default",
            "remote": False,
            "host": {
                "address": "localhost",
            },
            "components": {
                "scenario": {"uuid": "default-scenario", "address": "127.0.0.1:8957"},
                "monitor": {"uuid": "default-monitor", "address": "127.0.0.1:8958"},
                "broker": {"uuid": "default-broker", "address": "127.0.0.1:8956"},
            },
        }
        self._environments["umbra-default"] = env_default

    def _get_default_env_scenario(self):
        return self._environments["umbra-default"]

    def get_model(self):
        return self.model

    def get_umbra(self):
        return self.umbra

    def get_settings(self):
        return self.settings

    def get_model_settings(self):
        return self.model_settings

    def add_environment(self, env):
        env_id = env.get("id")

        if env_id not in self._environments:
            self._environments[env_id] = env

    def get_environments(self):
        return self._environments

    def get_default_environment(self):
        default_env = self._environments.get("umbra-default")
        return default_env

    def get(self):
        return self.topo

    def load_base(self, filename):
        self.graph = self.retrieve_graph(filename, base=True)
        if self.graph:
            return True
        return False

    def store(self):
        self.build()
        self.graph.graph["name"] = self.name
        self.graph.graph["model"] = self.model
        self.graph.graph["umbra"] = self.umbra
        self.graph.graph["settings"] = self.settings
        self.graph.graph["profile"] = self.profile.dump()
        self.graph.graph["lifecycle"] = self.lifecycle.dump()
        self.graph.graph["environments"] = self._environments
        ack = self.save_graph(self.graph, self.name)
        return ack

    def parse(self, data):
        super(Topology, self).parse(data)
        if self.graph:
            self.fill(data)
            return True
        return False

    def fill(self, data=None):
        data = data if data else self.graph.graph
        self.name = data.get("name", None)
        self.model = data.get("model", None)
        self.settings = data.get("settings", None)
        self.umbra = data.get("umbra", {})
        profile = data.get("profile", {})
        self.profile = Profile(self.name)
        self.profile.load(profile)
        lifecycle = data.get("lifecycle", {})
        self.lifecycle = Lifecycle(self.name)
        self.lifecycle.load(lifecycle)
        self._environments = data.get("environments", {})

    def load(self, filename):
        self.graph = self.retrieve_graph(filename)
        if self.graph:
            self.fill()
            return True
        return False

    def add_node(self, node_name, node_type, node_profile, **kwargs):
        node_attribs = {
            "name": node_name,
            "type": node_type,
            "profile": node_profile,
        }
        node_attribs.update(kwargs)
        self.graph.add_node(node_name, **node_attribs)

    def add_link_nodes(
        self, src, dst, link_type, link_profile, params_src=None, params_dst=None
    ):
        link_attribs = {
            "src": src,
            "dst": dst,
            "type": link_type,
            "profile": link_profile,
            "params_src": params_src,
            "params_dst": params_dst,
        }
        self.graph.add_edge(src, dst, **link_attribs)

    def create_profile(self, profile_name):
        self.profile = Profile(profile_name)

    def create_node_profile(self, cpus, memory, disk):
        node_resources = self.profile.build_node_resources(cpus, memory, disk)
        return node_resources

    def create_link_profile(self, bw, delay, loss):
        link_resources = self.profile.build_link_resources(bw, delay, loss)
        return link_resources

    def create_node_lifecycle(self, workflow, parameters, method, implementation):
        workflow = self.lifecycle.build_node_workflow(
            workflow, parameters, method, implementation
        )
        return workflow

    def add_node_lifecycle(self, workflows, node_name):
        if node_name in self.graph.nodes:
            self.lifecycle.add_node(workflows, node_name)
        else:
            logger.error(
                "Lifecycle not added: node_name %s does not exist in topology",
                node_name,
            )

    def add_node_profile(self, resources, profile=None, node_name=None):
        if profile or node_name:
            self.profile.add_node(resources, profile, node_name=node_name)
        else:
            logger.error("Node profile not added. Please, provide node type or name")

    def add_link_profile(self, resources, profile):
        if profile:
            self.profile.add_link(resources, profile)
        else:
            logger.error("Link profile not added. Please, provide link profile")

    def set_lifecycle(self, lifecycle):
        self.lifecycle = lifecycle

    def set_profile(self, profile):
        self.profile = profile

    def get_profile(self):
        return self.profile

    def show(self):
        logger.info("*** Dumping network graph ***")
        logger.info("nodes:")
        for n, data in self.graph.nodes(data=True):
            logger.info(f"  node = {n}, data = {data}")

        logger.info("links:")
        for src, dst, data in self.graph.edges(data=True):
            print("src", src, "dst", dst, "data", data)

    def build_environments(self):
        logger.debug("Topology build environment")
        envs = {}

        switches = []
        for n, data in self.graph.nodes(data=True):
            node = data
            if node.get("type") == "switch":
                switches.append(n)

        logger.debug(f"Node switches: {switches}")

        for sw in switches:
            sw_data = self.graph.nodes[sw]

            logger.debug(f"Node switch {sw} data: {sw_data}")

            sw_env = sw_data.get("environment")

            if sw_env not in envs:
                envs[sw_env] = {
                    "nodes": {},
                    "links": {},
                }

            envs[sw_env]["nodes"][sw] = sw_data

            for sw_neigh in self.graph.neighbors(sw):
                sw_edge_data = self.graph.get_edge_data(sw, sw_neigh, 0)
                sw_edge_type = sw_edge_data.get("type")

                link_id = sw + "-" + sw_neigh

                if sw_edge_type == "internal":
                    envs[sw_env]["links"][link_id] = sw_edge_data
                    sw_neigh_data = self.graph.nodes[sw_neigh]
                    envs[sw_env]["nodes"][sw_neigh] = sw_neigh_data

                if sw_edge_type == "external":
                    envs[sw_env]["links"][link_id] = sw_edge_data

        for n, data in self.graph.nodes(data=True):
            node = data
            if node.get("type") == "container":
                node_env = node.get("environment")

                if n not in envs[node_env]["nodes"]:
                    envs[node_env]["nodes"][n] = node

        return envs

    def build(self):
        nodes = {}
        links = {}

        for n, data in self.graph.nodes(data=True):
            node = data
            resources = self.profile.get_node(node)
            lifecycle = self.lifecycle.get_node(node)
            node.update(resources)
            node.update(lifecycle)
            node_id = node.get("name")
            nodes[node_id] = node

        for src, dst, data in self.graph.edges(data=True):
            link = data
            link["endpoints"] = (src, dst)
            resources = self.profile.get_link(link)
            if resources:
                link.update(resources)

            link_id = src + "-" + dst
            links[link_id] = link

        topo = {
            "nodes": nodes,
            "links": links,
        }

        topo["name"] = self.name
        topo["model"] = self.model
        topo["umbra"] = self.umbra
        topo["settings"] = self.settings
        topo["profile"] = self.profile.dump()
        topo["lifecycle"] = self.lifecycle.dump()
        topo["environments"] = self._environments

        self.topo = topo
        return topo

    def has(self, cat, name):
        if cat == "node":
            ack = name in self.graph.nodes()
        elif cat == "link":
            ack = name in self.graph.edges()
        else:
            ack = False
        return ack

    def get_data(self, cat, name):
        info = None
        if self.has(cat, name):
            if cat == "node":
                info = self.graph.nodes[name]
            if cat == "link":
                info = self.graph.edges[name]
        return info

    def fill_hosts_config(self, hosts_info):
        for n, data in self.graph.nodes(data=True):
            if n in hosts_info.keys():
                data["deploy"] = hosts_info.get(n)

    def fill_config(self, deploy_config):
        hosts = deploy_config.get("hosts")
        switches = deploy_config.get("switches")
        links = deploy_config.get("links")

        for n, data in self.graph.nodes(data=True):
            if n in hosts.keys():
                data["deploy"] = hosts.get(n)
            elif n in switches.keys():
                data["deploy"] = switches.get(n)
            else:
                logger.debug("unknown node %s", n)

        for link in links.values():
            src, dst = link.get("src"), link.get("dst")
            if (src, dst) in self.graph.edges():
                data = self.graph.get_edge_data(src, dst, 0)
                data["deploy"] = link

    def get_link_deploy_data_as(self, src, dst):
        if (src, dst) in self.graph.edges():
            data = self.graph.get_edge_data(src, dst, 0)
            data_src, data_dst = (
                data.get("deploy").get("src"),
                data.get("deploy").get("dst"),
            )

            if data_src == src:
                return data
            else:
                src_port = data.get("deploy").get("src-port")
                dst_port = data.get("deploy").get("dst-port")
                inv_data = {
                    "deploy": {
                        "src": dst,
                        "dst": src,
                        "name": "eth1<->s2-eth1",
                        "src-port": dst_port,
                        "dst-port": src_port,
                    }
                }
                return inv_data

    def get_host_intf_addr(self, path):
        host_dst = path[-1]

        end_src, end_dst = path[-2], path[-1]
        end_data = self.get_link_deploy_data_as(end_src, end_dst)
        dst_host_intf = end_data.get("deploy").get("dst-port")

        host_dst_data = self.graph.nodes[host_dst]
        intf_control_info = (
            host_dst_data.get("deploy").get("control").get(dst_host_intf)
        )
        nw_dst_ip = intf_control_info.get("ip")  # , intf_control_info.get("mask")
        return nw_dst_ip

    def get_deploy_map(self, path):
        host_src, host_dst = path[0], path[-1]

        deploy_map = {}

        nw_dst_ip = self.get_host_intf_addr(path)

        for i in range(1, len(path[:-1])):

            prev_src, prev_dst = path[i - 1], path[i]
            curr_src, curr_dst = path[i], path[i + 1]

            if (prev_src, prev_dst) in self.graph.edges() and (
                curr_src,
                curr_dst,
            ) in self.graph.edges():
                prev_data = self.get_link_deploy_data_as(prev_src, prev_dst)
                curr_data = self.get_link_deploy_data_as(curr_src, curr_dst)

                prev_deploy = prev_data["deploy"]
                src_port = prev_deploy.get("dst-port")

                curr_deploy = curr_data["deploy"]
                dst_port = curr_deploy.get("src-port")

                sw_data = self.graph.nodes[curr_src]

                deploy_src_port = sw_data.get("deploy").get("intfs").get(src_port)
                deploy_dst_port = sw_data.get("deploy").get("intfs").get(dst_port)

                sw_dpid = sw_data.get("deploy").get("dpid")

                deploy_map[i] = {
                    "dpid": sw_dpid,
                    "in_port": deploy_src_port,
                    "out_port": deploy_dst_port,
                    "nw_dst_ip": nw_dst_ip,
                }

        return deploy_map

    def read_file(self, filepath):
        data = {}
        try:
            with open(filepath, "r") as f:
                data = load(f, Loader=yaml.SafeLoader)
        except Exception as e:
            logger.debug("exception: could not read file %s - %s", filepath, e)
        finally:
            return data

    def write_file(self, data, filepath):
        noalias_dumper = yaml.dumper.SafeDumper
        noalias_dumper.ignore_aliases = lambda self, data: True
        try:
            with open(filepath, "w") as f:
                dump(
                    data,
                    f,
                    indent=4,
                    default_flow_style=False,
                    explicit_start=True,
                    Dumper=noalias_dumper,
                )
                # dump(data, f, default_flow_style=False)
        except Exception as e:
            logger.debug("exception: could not write file %s - %s", filepath, e)
        else:
            logger.debug("write file ok %s - \n%s", filepath, data)

    def _join_full_path(self, temp_dir, filename):
        return os.path.normpath(
            os.path.join(os.path.dirname(__file__), temp_dir, filename)
        )

    def _full_path(self, temp_dir):
        return os.path.normpath(os.path.join(os.path.dirname(__file__), temp_dir))


class EventsFabric:
    def __init__(self):
        self._ids = 1
        self._events = {}

    def get(self):
        return self._events

    def add(self, when, category, params):
        ev_id = self._ids
        event = {
            "ev": ev_id,
            "when": when,
            "category": category,
            "params": params,
        }
        self._events[ev_id] = event
        self._ids += 1

    def build(self):
        return self._events

    def parse(self, data):
        self._events = data


class Events:
    """
    Use this Event class for event category of: monitor, agent, and environment
    """

    def __init__(self):
        self._ev_id = 1
        self._events = defaultdict(lambda: [])
        self._events_by_category = defaultdict(lambda: [])

    def get_by_category(self, category):
        return self._events_by_category.get(category, {})

    def get(self):
        return self._events

    def add(self, schedule, category, ev_args, **kwargs):
        """
        Input for kwargs:

        'until': time (in sec) limit to complete this event
        'duration': expected time to complete an iteration, if 'repeat'
            is set to run more than once
        'interval': delay for the next iteration if 'repeat' is set
        'repeat': repeat the cmd by 'x' iteration. Set to 0 to run
            command only once

        """
        sched = {"from": 0, "until": 0, "duration": 0, "interval": 0, "repeat": 0}
        sched.update(schedule)

        ev_id = self._ev_id
        event = {
            "id": ev_id,
            "schedule": sched,
            "category": category,
            "event": ev_args,
        }
        self._events[ev_id] = event
        self._events_by_category[category].append(event)
        self._ev_id += 1

    def build(self):
        return self._events

    def parse_by_category(self):
        for ev in self._events.values():
            category = ev.get("category")
            self._events_by_category[category].append(ev)

    def parse(self, data):
        self._events = data
        self.parse_by_category()


class Experiment:
    def __init__(self, name):
        self.name = name
        self.folder = "/tmp/umbra/"
        self.folder_settings = "/tmp/umbra/"
        self.topology = None
        self.events = Events()

    def parse(self, data):
        topo = Topology(None, None)
        ack = topo.parse(data.get("topology", {}))
        if ack:
            self.topology = topo
            self.events.parse(data.get("events", {}))
            self.name = data.get("name", None)
            return True
        return False

    def add_event(self, sched, category, event):
        self.events.add(sched, category, event)

    def set_topology(self, topology):
        self.topology = topology
        self.folder_settings = topology.get_settings()
        self.folder = topology.get_model_settings()

    def get_topology(self):
        return self.topology

    def dump(self):
        topo_built = self.topology.build()
        events_built = self.events.build()
        experiment = {
            "name": self.name,
            "topology": topo_built,
            "events": events_built,
        }
        return experiment

    def save(self):
        data = self.dump()
        filename = self.name + ".json"

        filepath = os.path.normpath(os.path.join(self.folder, filename))

        with open(filepath, "w") as outfile:
            logger.info("Saving experiment config file %s", filepath)
            json.dump(data, outfile, indent=4, sort_keys=True)
            print("\n")
            print("\t\t############ umbra-design ################\t\t")
            print("\t Experiment saved at", filepath)
            print("\t Experiment settings in ", self.folder_settings)
            print("\t\t############ umbra-design ################\t\t")
            print("\n")
            return True

    def load(self, cfg_name):
        filename = cfg_name + ".json"

        filepath = os.path.normpath(os.path.join(self.folder, filename))

        with open(filepath, "r") as infile:
            data = json.load(infile)
            self.parse(data)
