import logging

logger = logging.getLogger(__name__)

import functools
import asyncio
import time

from umbra_cfgs.config import Topology, Scenario
from umbra_orch.store import Storage
from umbra_orch.plugins.fabric import FabricEvents


class Paths:
    def __init__(self):
        self.scenario = None
        self.topology = None

    def set_cfg(self, scenario, topology):
        self.scenario = scenario
        self.topology = topology

    def build_flow(self, info):
        logger.info("build_flow %s", info)

        flow = {
            "dpid": int(info.get("dpid")),
            "cookie": 1,
            "cookie_mask": 1,
            "table_id": 0,
            "idle_timeout": 0,
            "hard_timeout": 0,
            "priority": 1,
            "flags": 1,
            "match": {
                "in_port": info.get("in_port"),
                "nw_dst": info.get("nw_dst_ip"),
                "dl_type": 2048,
            },
            "instructions": [
                {
                    "type": "APPLY_ACTIONS",
                    "actions": [
                        {
                            "max_len": 65535,
                            "port": info.get("out_port"),
                            "type": "OUTPUT"
                        }
                    ]
                }
            ]
        }
        return flow

    def build_flows(self, deploy_map):
        flows = []
        for i,info in deploy_map.items():
            flow = self.build_flow(info)
            flows.append(flow)
        return flows

    def get_flows(self, event):
        flows = []
        params = event.get("params")
        event_type = params.get("type")

        if event_type == "p2p":
            path = params.get("hops")
            deploy_map = self.topology.get_deploy_map(path)
        if event_type == "shortest":
            (src, dst) = params.get("hops")
            path = self.topology.shortest_path(src, dst)
            deploy_map = self.topology.get_deploy_map(path)
        
        if deploy_map:
            flows = self.build_flows(deploy_map)
        return flows

    def build_paths_msgs(self, event):
        logger.info("build path msgs")
        msgs = []
        paths_mng_url = self.scenario.management.get("paths")

        flows = self.get_flows(event)
        for flow in flows:
            msg = {
                "when": event.get("when", "now"),
                "to": paths_mng_url,
                "data": flow,
            }                
            msgs.append(msg)
        return msgs


class Messages:
    def __init__(self):
        self._sent = {}
        self._ack = {}
    
    def wait(self, msg):
        ev = msg.get("ev")
        self._sent[ev] = msg
        logger.info("Wait %s", ev)


    def queued(self):
        evs_ack = self._ack.keys()
        queued = [ev for ev in self._sent.keys() if ev not in evs_ack]
        logger.info("Queued %s", queued)
        return queued

    def ack(self, msg):
        ev = msg.get("ev")
        if ev in self._sent:
            self._ack[ev] = msg
            logger.info("Ack %s", ev)
            return True
        return False

    def get(self, ev):
        if ev in self._ack:
            metrics = self._ack[ev]
            event = self._sent[ev]
            return (event, metrics)
        return None


class Operator:
    def __init__(self, conf, event_loop, exit_call):
        self.conf = conf
        self.asyncio_loop = event_loop
        self.exit_call = exit_call
        self.scenario = None
        self.topology = None
        self.paths = Paths()
        self.msgs = Messages()
        self.storage = Storage()
        self.events_fabric = FabricEvents(self.asyncio_loop)
        self.plugins = {}

    def callback(self):
        callback = "http://" + self.conf.host + ":" + self.conf.port + "/"
        return callback

    def format_target(self, target_ip):
        _to = "http://" + target_ip + ":9091" + "/"
        return _to

    def build_instructions_msgs(self, info, event):
        msgs = []
        params = event.get("params")
        targets = params.get("targets")
        for target in targets:
            if target in info.keys():
                target_ip = info.get(target).get("management").get("ip")
                to = self.format_target(target_ip)

                data = {
                    "ev": event.get("ev"),
                    "instructions":  params.get("instructions"),
                    "callback": self.callback(),
                }

                msg = {
                    "when": event.get("when", "now"),
                    "to": to,
                    "data": data,
                }
                msgs.append(msg)
        return msgs

    def build_topology_msgs(self, event):
        topo_mng_url = self.scenario.management.get("topology")
        params = event.get("params")
        evs = {
            "ev": event.get("ev"),
            "group": params.get("group"),
            "targets": params.get("targets"),
            "specs": params.get("specs"),
        }
        
        msg = {
            "when": event.get("when", "now"),
            "to": topo_mng_url,
            "data": {
                "type": "events",
                "events": [evs],
            }
        }
        logger.info("topology msg %s", msg)
        return msg

    def build_stats_msgs(self, event):
        logger.info("build stat messages")
        
        stats_mng_url = self.scenario.management.get("stats")
        params = event.get("params")

        data = {}
        data["ev"] = event.get("ev")                    
        data["callback"] = self.callback()
        data["specs"] = params.get("specs")
        data["query_flows"] = True if params.get("type") == "flows" else False
        data["query_ports"] = True if params.get("type") == "ports" else False
        
        targets = params.get("targets")
        target_ids = []
        for target in targets:
            if self.topology.has("node", target):
                info = self.topology.get_data("node", target)
                if info:
                    logger.debug("Target info %s", info)
                    deploy = info.get("deploy")
                    if deploy:
                        dpid = deploy.get("dpid")
                        target_ids.append(dpid)
                        logger.debug("Target %s in set - dpid %s", target, dpid)
                else:
                    logger.debug("Target Info %s not in set", target)
            else:
                logger.debug("Target %s not in nodes set", target)

        data["targets"] = target_ids

        msg = {
            "when": event.get("when", "now"),
            "to": stats_mng_url,
            "data": data
        }
        return msg

    def build_deployment_msgs(self, event):
        stats_mng_url = self.scenario.management.get("deployment")
        data = event.get("params")
        data["callback"] = self.callback()
        data["ev"] = event.get("ev")                    

        msg = {
            "when": event.get("when", "now"),
            "to": stats_mng_url,
            "data": data
        }
        return msg

    def build_infrastructure_msgs(self, event):
        infrastructure_mng_url = self.scenario.management.get("infrastructure")
        
        data = {
            "ev": event.get("ev"),
            "instructions": {1:event.get("params")},
            "callback": self.callback()
        }
        
        msg = {
            "when": event.get("when", "now"),
            "to": infrastructure_mng_url,
            "data": data
        }
        return msg

    def sched_msgs(self, msgs):
        for msg in msgs:
            when = msg.get("when")
            logger.info("Calling at %s msg to %s", when, msg.get("to"))
            logger.debug("%s", msg.get("data"))
            self.call_at(when, self.call, msg)
    
    def config_plugins(self):
        logger.info("Configuring Umbra plugins")
        umbra_cfgs = self.topology.umbra
        plugin = umbra_cfgs.get("plugin")
        
        if plugin == "fabric":
            logger.info("Configuring Fabric plugin")
            topology = umbra_cfgs.get("topology")
            configtx = umbra_cfgs.get("configtx")
            configsdk = umbra_cfgs.get("configsdk")
            chaincode = umbra_cfgs.get("chaincode")
            ack_fabric = self.events_fabric.config(topology, configsdk, chaincode, configtx)
            if ack_fabric:
                self.plugins["fabric"] = self.events_fabric
    
    def set_cfg(self, scenario, info_deploy):
        self.scenario = scenario
        info_topology = info_deploy.get("topology")
        info_hosts = info_deploy.get("hosts")

        topo = self.scenario.get_topology()
        topo.fill_config(info_topology)
        topo.fill_hosts_config(info_hosts)
        self.topology = topo
        self.config_plugins()

    def schedule_plugins(self, events):
        for name,plugin in self.plugins.items():
            logger.info("Scheduling plugin %s events", name)
            plugin.schedule(events)

    def schedule(self, scenario, config_info):
        logger.info("Scheduling messages")
        msgs = []
        
        mngment = config_info.get("management")
        info_hosts = mngment.get("hosts")
        
        self.scenario = Scenario(None, None)
        self.scenario.parse(scenario)
        self.set_cfg(self.scenario, mngment)
        self.paths.set_cfg(self.scenario, self.topology)
        
        events = scenario.get("events")
        logger.info('events %s', events)

        for _id,event in events.items():
            event_category = event.get("category")
            
            if event_category == "calls":
                ev_msgs = self.build_instructions_msgs(info_hosts, event)
                msgs.extend(ev_msgs)
            
            if event_category == "paths":
                ev_msgs = self.paths.build_paths_msgs(event)
                msgs.extend(ev_msgs)

            elif event_category == "topology":
                ev_msg = self.build_topology_msgs(event)
                msgs.append(ev_msg)

            elif event_category == "stats":
                ev_msg = self.build_stats_msgs(event)
                msgs.append(ev_msg)

            elif event_category == "deployment":
                ev_msg = self.build_deployment_msgs(event)
                msgs.append(ev_msg)

            elif event_category == "infrastructure":
                ev_msg = self.build_infrastructure_msgs(event)
                msgs.append(ev_msg)

        self.sched_msgs(msgs)
        self.schedule_plugins(events)

    def run_callback(self, callback):
        try:
            outputs = callback()
            self.asyncio_loop.create_task(self.exit_call(outputs))
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.error("Exception in callback %r", callback, exc_info=True)
    
    def sched_time(self, when):
        if type(when) is float:
            if when >= time.time():
                rel_when = when - time.time()
            else:
                rel_when = 0
        elif type(when) is str:
            if when == "now":
                rel_when = 0
            else:
                rel_when = float(when)
        else:
            rel_when = 0
        return rel_when

    def call_at(self, when, callback, *args, **kwargs):
        rel_when = self.sched_time(when)
        self.asyncio_loop.call_later(
            max(0, rel_when), self.run_callback,
            functools.partial(callback, *args, **kwargs))

    def call(self, *args, **kwargs):
        #Only if some callback is needed
        # logger.info("Sending message")
        for arg in args:
            self.msgs.wait(arg.get("data"))
        return args

    def process_event(self, data):
        ev = data.get("ev")
        contents = self.msgs.get(ev)
        if contents:
            (event, metrics) = contents
            logger.info("Storing event %s - metrics %s", event, metrics)

    def events(self, data):
        if self.msgs.ack(data):
            self.process_event(data)
        self.msgs.queued()
        