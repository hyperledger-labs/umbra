#!/usr/bin/python
import exceptions
import subprocess
import re
import os
import yaml
import shutil
import logging
import time
import psutil        
import signal

from multiprocessing import Process

from mininet.net import Containernet
from mininet.node import RemoteController, Controller, Docker, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Link
from mininet import clean

# LOG = logging.getLogger(os.path.basename(__file__))
LOG = logging.getLogger(__name__)

setLogLevel('info')
# others
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("docker").setLevel(logging.WARNING)


# wait after start scripts are triggered
TRIGGER_DELAY = 3


class Experiment:
    def __init__(self, run_id, parameter, cli_mode=False):
        self.run_id = run_id
        self.scenario = parameter
        self.cli_mode = cli_mode
        self.net = None
        self.nodes = {}
        self.switches = {}
        self.containers = []
        self.switch_links = {}
        self.config_sw_links = {}
        self.topo_parsed = {}

    def build(self):
        topo = self.scenario.get("topology")
        topo_parsed = self._parse_topo(topo)
        self.topo_parsed = topo_parsed
        # print(topo_parsed)

    def start(self, cli_mode=False):
        # split down experiments in small steps that can be overwritten subclasses
        self._create_network()
        self._add_containers()
        self._add_switches()
        self._add_links()
        self._start_network()
        # self._config_switches()
        LOG.info("Experiment %s running." % (self.run_id))
        
        info = {}
        hosts_info = self.hosts_management_info()
        self._trigger_container_scripts("start", hosts_info)
        
        info["hosts"] = hosts_info
        info["topology"] = self.net_topo_info()
        return info

    def stop(self):
        # maybe call stop in self._trigger_container_scripts(cmd="./stop.sh")
        self._stop_network()
        self._stop_processes()
        self.mn_cleanup()
        self.topo_parsed = {}

    def update_link_resources(self, src, dst, resources):
        src = self.net.get(src)
        dst = self.net.get(dst)
        links = src.connectionsTo(dst)
        srcLink = links[0][0]
        dstLink = links[0][1]
        srcLink.config(**resources)
        dstLink.config(**resources)

    def update_link(self, src, dst, online, resources):
        ack = False
        if online:
            self.net.configLinkStatus(src, dst, "up")
            ack = True

            if resources:
                self.update_link_resources(src, dst, resources)
                ack = True
        else:
            self.net.configLinkStatus(src, dst, "down")
            ack = True
        return ack
        
    def update(self, events):
        ack = False

        if self.net:
            LOG.info("Updating network: %r" % self.net)
            LOG.info("Events: %s", events)
            
            for ev in events:
                ev_group = ev.get("group")
                ev_specs = ev.get("specs")
                
                if ev_group == "links":
                    act = ev_specs.get("action")
                                        
                    if act == "update":
                        online = ev_specs.get("online")
                        resources = ev_specs.get("resources", None)
                        (src, dst) = ev.get("targets")
                        ack = self.update_link(src, dst, online, resources)
        return ack

    def mn_cleanup(self):
        # mininet cleanup
        clean.cleanup()

    def _stop_processes(self):
        LOG.info("stopping processes")
        nodes_topo = self.topo_parsed.get("nodes")
        for node_id in self.nodes:
            node_req = nodes_topo.get(node_id, None)
            if node_req:
                image_format = node_req.get("image_format")
                if image_format == "process":
                    node_process = self.nodes[node_id]
                    LOG.info("stopping processes node_id %s alive %s", node_id, node_process.is_alive())
                    # node_process.terminate()
                    # LOG.info('node_id %s process stopped %s', node_id, node_process.is_alive())
                    # node_process.kill()
                    if node_process.poll() is None:
                        os.killpg( node_process.pid, signal.SIGHUP )
                        node_process.wait()

                    LOG.info('node_id %s process stopped %s', node_id, node_process.is_alive())

    def parse_info(self, elements, specie):
        full_info = {}
        if specie == "hosts":
            full_info["hosts"] = {}
            for host in elements:
                info = {
                    "name": host.name,
                    "intfs":  dict( [(intf.name,port) for (intf,port) in host.ports.items()] ), 
                }
                full_info["hosts"][host.name] = info

        if specie == "switches":
            full_info["switches"] = {}
            for sw in elements:
                info = {
                    "name": sw.name,
                    "dpid": sw.dpid,
                    "intfs":  dict( [(intf.name,port) for (intf,port) in sw.ports.items()] ), 
                }
                full_info["switches"][sw.name] = info

        if specie == "links":
            full_info["links"] = {}
            for link in elements:
                link_name = str(link)
                info = {
                    "name": link_name,
                    "src": link.intf1.node.name,
                    "dst": link.intf2.node.name,
                    "src-port": link.intf1.name,
                    "dst-port": link.intf2.name,
                }
                full_info["links"][link_name] = info
        return full_info

    def net_topo_info(self):
        info = {}
        info.update(self.parse_info(self.net.hosts, "hosts"))
        info.update(self.parse_info(self.net.switches, "switches"))
        info.update(self.parse_info(self.net.links, "links"))
        LOG.info("Topology info %s", info)
        return info

    def _create_network(self):
        # self.net = Containernet(autoStaticArp=True, controller=RemoteController)
        # c1 = RemoteController( 'c1', ip='127.0.0.1', port=6653, protocols=["OpenFlow13"] )
        # self.net.addController(c1)        
        self.net = Containernet(autoStaticArp=True, controller=Controller)
        self.net.addController('c0')
        # LOG.info("Created network: %r" % self.net)

    def _add_switches(self):
        switches = self.topo_parsed.get("switches")
        for sw_name in switches:
            s = self.net.addSwitch(sw_name)
            self.switches[sw_name] = s

    def _add_containers(self):
        nodes = self.topo_parsed.get("nodes")
        for node_id, node in nodes.items():
            image_format = node.get("image_format")
            if image_format == "docker":
                added_node = self._new_container(
                    node_id,
                    node.get("addr_input", None),
                    node.get("image"),
                    cpu_cores=node.get("cpus", None),
                    cpu_bw=node.get("cpu_bw", 1.0),
                    mem=node.get("memory"),
                    volumes=node.get("volumes", []),
                    environment=node.get("env", None),
                    ports=node.get("ports", []),
                    port_bindings=node.get("port_bindings", {}),
                    command=node.get("command", None),
                    working_dir=node.get("working_dir", None),
                    extra_hosts=node.get("extra_hosts", {}),
                    network_mode=node.get("network_mode", "none"),
                )
                self.nodes[node_id] = added_node
            elif image_format == "process":
                added_node = self._new_process(node_id, node.get("entrypoint"))
                self.nodes[node_id] = added_node
            else:
                LOG.info("unknown node_id %s image_format %s", node_id, image_format)

    def _add_links(self):
        links = self.topo_parsed.get("links")

        for link_id, link in links.items():        
            link_type = link.get("type")

            if link_type == "E-Line":
                src = link.get("src")
                dst = link.get("dst")

                params_src = {}
                params_dst = {}
                intf_src = None
                intf_dst = None

                params_s = link.get("params_src", {})
                params_d = link.get("params_dst", {})
                
                link_resources = link.get("resources", {})
                if params_s:
                    intf_src = params_s.get("id", None)
                    ip_src = params_s.get("ip", None)
                    if ip_src:
                        params_src["ip"] = str(ip_src)

                if params_d:
                    intf_dst = params_d.get("id", None)
                    ip_dst = params_d.get("ip", None)
                    if ip_dst:
                        params_dst["ip"] = str(ip_dst) 

                src_node = self.nodes.get(src) if src in self.nodes.keys() else self.switches.get(src)
                dst_node = self.nodes.get(dst) if dst in self.nodes.keys() else self.switches.get(dst)

                LOG.info("adding link src %s - intf_src %s, dst %s, intf_dst %s, params_src %s, params_dst %s, resources %s", 
                            src, intf_src, dst, intf_dst, params_src, params_dst, link_resources)
                
                link_stats = self.net.addLink(src_node, dst_node,
                                                intfName1=intf_src, intfName2=intf_dst,
                                                params1=params_src, params2=params_dst,
                                                cls=TCLink, **link_resources)

                LOG.info("Status %s", link_stats)

                # if params_s:
                #     intf = src_node.intf(intf=intf_src)
                #     ip, mask = params_s.get("ip").split("/")
                #     int_stats = src_node.setIP(ip, prefixLen=int(mask), intf=intf)
                #     LOG.info("set intf_name %s intf %s - ip %s", intf_src, intf, params_s.get("ip") )
                #     LOG.info("int_stats %s", int_stats)

                # if params_d:
                #     intf = dst_node.intf(intf=intf_dst)
                #     ip, mask = params_d.get("ip").split("/")
                #     int_stats = dst_node.setIP(ip, prefixLen=int(mask), intf=intf)
                #     LOG.info("set intf_name %s intf %s - ip %s", intf_dst, intf, params_d.get("ip") )
                #     LOG.info("int_stats %s", int_stats)

    def _start_network(self):
        if self.net:
            self.net.start()
            LOG.info("Started network: %r" % self.net)

    def _config_sw_flow(self, sw_id, params):
        LOG.info("_config_sw_flow %s", params)
        cmd = "add-flow in_port={src},actions=output:{dst}".format(**params)
        cmd_args = cmd.split(' ')
        sw = self.switches.get(sw_id)
        ack = sw.dpctl(*cmd_args)
        # LOG.info("ack %s", ack)

    def _get_sw_port(self, sw, port_name):
        # LOG.info("_get_sw_port %s", port_name)
        cmd = "find interface name={0}"
        cmd = cmd.format(port_name)
        cmd_args = cmd.split(' ')
        stats_port = sw.vsctl(*cmd_args)
        regex='ofport\s+:\s+([0-9]+)'
        of_ports = re.findall(regex, stats_port)
        of_port = of_ports.pop()
        return of_port

    def _config_map_ports_sw(self, sw_id, adjs):
        # LOG.info("_config_map_ports_sw sw_id %s, adjs %s", sw_id, adjs)
        maps = []
        sw = self.switches.get(sw_id)
        sw_links = self.switch_links.get(sw_id)
        # LOG.info("sw_links %s", sw_links)
        default = {'src': None, 'dst': None}

        for stats in adjs:
            sw_port = stats.intf1.name
            host_port = stats.intf2.name
            # LOG.info("sw link port1 %s port2 %s", sw_port, host_port)
            port_num = self._get_sw_port(sw, sw_port)
            for sw_link in sw_links:
                src = sw_link.get("src")
                dst = sw_link.get("dst")
                if host_port == src:
                    default['src'] = port_num
                    # LOG.info("default['src'] %s = host_port %s port_num %s", sw_port, host_port, port_num)
                if host_port == dst:
                    default['dst'] = port_num
                    # LOG.info("default['dst'] %s = host_port %s port_num %s", sw_port, host_port, port_num)
        maps.append(default)
        # LOG.info("maps %s", maps)
        return maps

    def _config_switches(self):
        LOG.info("_config_switches")
        for sw_id,adjs in self.config_sw_links.items():
            map_sw_ports = self._config_map_ports_sw(sw_id,adjs)
            for map_ports in map_sw_ports:
                self._config_sw_flow(sw_id, map_ports)

    def format_host_entrypoint(self, node_id, entrypoint, hosts_info, configuration):
        node_info = hosts_info.get(node_id)
        node_ip = node_info.get("management").get("ip")               
        fmt_kwargs = {'host_id': node_id, 'host_ip': node_ip}
        if configuration:
            fmt_kwargs['configuration'] = configuration
        LOG.info("fmt_kwargs %s", fmt_kwargs)
        fmt_entrypoint = entrypoint.format(**fmt_kwargs)
        return fmt_entrypoint

    def format_params(self, call, node_id, params, hosts_info):
        if node_id in hosts_info:
            node_info_full = hosts_info.get(node_id)
            node_info = node_info_full.get("management")

            for key,value in params.items():
                if "get_attrib" in value:
                    _, param = value.split(":")
                    
                    node_param = node_info.get(param, None) 
                    if node_param:
                        params[key] = node_param

    def _trigger_container_scripts(self, call, hosts_info):
        LOG.debug("call container lifecycle workflows")
        nodes_topo = self.topo_parsed.get("nodes")
        for node_id, node_instance in self.nodes.items():
            node_req = nodes_topo.get(node_id, None)
            if node_req:
                node_life = node_req.get("lifecycle")
                if node_life:
                    workflows = [workflow for workflow in node_life if workflow.get("workflow") == call]

                    for workflow in workflows:
                        params = workflow.get("parameters")
                        implementation = workflow.get("implementation")
                        self.format_params(call, node_id, params, hosts_info)
                        cmd = implementation.format(**params)                   
                        node_instance.cmd(cmd)
                        LOG.debug("Triggered %r in container %r" % (cmd, node_instance))
        
        time.sleep(TRIGGER_DELAY)

    def _stop_network(self):
        if self.net:
            self.net.stop()
            LOG.info("Stopped network: %r" % self.net)

    def wait_experiment(self, wait_time):
        LOG.info("Experiment %s running. Waiting for %d seconds." % (self.run_id , wait_time))
        time.sleep(wait_time)
        LOG.info("Experiment done.")

    def _parse_topo(self, topo):
        topo_parsed = {}
        topo_parsed["nodes"] = {}       
        topo_parsed["links"] = {}
        topo_parsed["switches"] = []

        nodes = topo.get("nodes")
        links = topo.get("links")

        for node in nodes:
            node_id = node.get("name")
            node_type = node.get("type")
        
            if node_type == "container":
                node_image = node.get("image")
               
                topo_parsed["nodes"][node_id] = {
                    "image": node_image,
                    "image_format": "docker",
                    "lifecycle": node.get("lifecycle", []),
                    "env": node.get("env", []),
                    "volumes": node.get("volumes", []),
                    "ports": node.get("ports", []),
                    "port_bindings": node.get("port_bindings", {}),
                    "working_dir": node.get("working_dir", None),
                    "command": node.get("command", None),
                    "extra_hosts": node.get("extra_hosts", {}),
                    "network_mode": node.get("network_mode", "none")
                }
                
                req_res = node.get("resources")
                node_res = {
                    "cpus": req_res.get("cpus", None),
                    "memory": req_res.get("memory", None),
                    "disk": req_res.get("disk", None)
                }
                
                topo_parsed["nodes"][node_id].update(node_res)


            elif node_type == "switch":
                topo_parsed["switches"].append(node_id)

            else:
                LOG.error("unknown node type %s", node_type)
        
        for link in links:
            link_type = link.get("type")

            link_src = link.get("src")
            link_dst = link.get("dst")
            
            src_type = 'switch' if link_src in topo_parsed['switches'] else 'container'
            dst_type = 'switch' if link_dst in topo_parsed['switches'] else 'container'

            if link_type == "E-Line":
                link_id = link_src+"-"+link_dst
                
                params_dst = link.get("params_dst")
                params_src = link.get("params_src")

                topo_parsed["links"][link_id] = {
                    'type': link_type,
                    'src_type': src_type,
                    'dst_type': dst_type,
                    'src': link_src,
                    'dst': link_dst,
                    'params_src': params_src,
                    'params_dst': params_dst,
                    'resources': link.get("resources", {})
                }

            else:
                LOG.info("unknown link type %s", link_type)

        return topo_parsed

    def _new_container(self, name, ip, image,
                        cpu_cores=None, cpu_bw=None, mem=None,
                        volumes=None, environment=None,
                        command=None, ports=[], working_dir=None, extra_hosts=None,
                        port_bindings=[], network_mode=None):
        """
        Helper method to create and configure a single container.
        """
        def calculate_cpu_cfs_values(cpu_bw):
            cpu_bw_p = 100000
            cpu_bw_q = int(cpu_bw_p*cpu_bw)
            return cpu_bw_p, cpu_bw_q

        # translate cpu_bw to period and quota
        cpu_bw_p, cpu_bw_q = calculate_cpu_cfs_values(cpu_bw)
        # create container
        c = self.net.addDocker(name,
           ip=ip,
           dimage=image,
        #    volumes=[os.path.join(os.getcwd(), self.out_path) + "share_" + name + ":/mnt/share:rw"],
           volumes=volumes,
           cpu_period=cpu_bw_p,
           cpu_quota=cpu_bw_q,
           cpuset_cpus=str(cpu_cores) if cpu_cores else '',
           mem_limit=str(mem) + "m",
           memswap_limit=0,
           environment=environment,
           dcmd=command,
           ports=ports,
           port_bindings=port_bindings,
           working_dir=working_dir,
           extra_hosts=extra_hosts, 
           network_mode=network_mode)

        # self.containers.append(c)
        # LOG.debug("Started container: %r" % str(c))
        return c

    def get_host_ip(self):
        intf = "docker0"
        intfs =  psutil.net_if_addrs()
        intf_info = intfs.get(intf, None)
        if intf_info:
            for address in intf_info:
                if address.family == 2:
                    host_address = address.address
                    return host_address
        return None        

    def process_args(self, cmd):
        args = cmd.split(" ")
        # p = subprocess.Popen(args,
        #                 stdin=subprocess.PIPE,
        #                 stdout=subprocess.PIPE,
        #                 stderr=subprocess.PIPE,
        #                 )
        subprocess.call(args)

    def _new_process(self, node_id, entrypoint):
        p = None
        node_ip = self.get_host_ip()
        fmt_kwargs = {'host_id': node_id, 'host_ip': node_ip}
        cmd_entrypoint = entrypoint.format(**fmt_kwargs)
        LOG.info("node_id %s - process args %s", node_id, cmd_entrypoint)
        try:
            # p = Process(target=self.process_args, args=(cmd_entrypoint,))
            # p.daemon = True
            # p.start()
            args = cmd_entrypoint.split(" ")
            p = subprocess.Popen(args,
                stdin = subprocess.PIPE,
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE,
                )            
        except OSError as e:
            LOG.info('ERROR: process could not be started %s', e)
        else:
            # LOG.info('node_id %s - cmd %s - pid %s - alive %s', node_id, cmd_entrypoint, p.pid, p.is_alive())
            LOG.info('node_id %s - cmd %s - pid %s', node_id, cmd_entrypoint, p.pid)
        finally:    
            return p        

    def get_host_intfs_ip(self, host, intf):
        config = host.cmd( 'ifconfig %s 2>/dev/null' % intf)
        # LOG.info("get host %s config ips %s", host, config)
        if not config:
            # LOG.info('Error: %s does not exist!\n', intf)
            return None
        ips = re.findall( r'\d+\.\d+\.\d+\.\d+', config )
        if ips:
            # LOG.info("host intf ips %s", ips)
            ips_dict = {'ip': ips[0], 'broadcast': ips[1], 'mask': ips[2]}
            return ips_dict
        return None

    def get_host_ips(self, host):
        mng_intf = 'eth0'
        
        info = {}
        
        mng_ips = self.get_host_intfs_ip(host, mng_intf)
        info["management"] = mng_ips
        info["control"] = {}

        ack = True
        i = 1
        while ack:
            intf = "eth" + str(i)
            ips = self.get_host_intfs_ip(host, intf)
            if ips:
                info["control"][intf] = ips
                i += 1
            else:
                ack = False
        return info
        
    def hosts_management_info(self):
        info = {}
        nodes = self.topo_parsed.get("nodes")
        for host_id,host in self.nodes.items():
            node_info = nodes.get(host_id)
            image_format = node_info.get("image_format")
            if image_format == "docker":
                ips = self.get_host_ips(host)
                info[host_id] = ips                    

            if image_format == "process":
                node_ip = self.get_host_ip()
                mngnt_ips = {'ip': node_ip}
                info[host_id] = {"management": mngnt_ips}

        return info


if __name__ == "__main__":
    pass