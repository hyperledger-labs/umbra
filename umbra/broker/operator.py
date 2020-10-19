import logging
import json
import asyncio
import functools
from datetime import datetime

from grpclib.client import Channel
from grpclib.exceptions import GRPCError

from google.protobuf import json_format

from umbra.common.protobuf.umbra_grpc import ScenarioStub, AgentStub, MonitorStub
from umbra.common.protobuf.umbra_pb2 import Report, Workflow, Instruction, Snapshot

from umbra.design.configs import Topology, Scenario
from umbra.broker.plugins.fabric import FabricEvents
from umbra.broker.plugins.env import EnvEventHandler

logger = logging.getLogger(__name__)

# port that umbra-agent binds to
AGENT_PORT = 8910

class Operator:
    def __init__(self, info):
        self.info = info
        self.scenario = None
        self.topology = None
        self.events_fabric = FabricEvents()
        self.events_env = EnvEventHandler()
        self.plugins = {}
        self.agent_plugin = {}

    def parse_bytes(self, msg):
        msg_dict = {}

        if type(msg) is bytes:
            msg_str = msg.decode('utf32')
            msg_dict = json.loads(msg_str)
        
        return msg_dict

    def serialize_bytes(self, msg):
        msg_bytes = b''

        if type(msg) is dict:
            msg_str = json.dumps(msg)
            msg_bytes = msg_str.encode('utf32')
            
        return msg_bytes

    def config_agent(self, deployed_topo, scenario):
        """
        Get agent(s) from 'scenario' and find its corresponding
        IP:PORT from the 'deployed_topo'

        Arguments:
            deployed_topo {dict} -- deployed topology from umbra-scenario
            scenario {dict} -- the user-defined scenario

        """
        logger.info("Configuring umbra-agent plugin")
        umbra_topo = scenario.get("umbra").get("topology")
        agents = umbra_topo.get("agents")

        deployed_hosts = deployed_topo.get("topology").get("hosts")

        for hostname, host_val in deployed_hosts.items():
            # tiny hack: e.g. umbraagent.example.com, strip the ".example.com"
            subdomain = hostname.split('.')[0]

            if subdomain in agents.keys():
                agent_ip = host_val.get("host_ip")
                self.agent_plugin[subdomain] = agent_ip + ":" + str(AGENT_PORT)
                logger.info("Added agent: agent_name = %s, at %s:%s",
                            subdomain, agent_ip, AGENT_PORT)

    async def call_scenario(self, test, command, topology, address):
        logger.info(f"Deploying Scenario - {command}")

        scenario = self.serialize_bytes(topology)
        deploy = Workflow(id=test, command=command, scenario=scenario)
        deploy.timestamp.FromDatetime(datetime.now())
        
        host, port = address.split(":")
        channel = Channel(host, port)
        stub = ScenarioStub(channel)
        status = await stub.Establish(deploy)

        if status.error:
            ack = False
            logger.info(f'Scenario not deployed error: {status.error}')
        else:
            ack = True
            logger.info(f'Scenario deployed: {status.ok}')

            info = self.parse_bytes(status.info)

        channel.close()

        return ack,info  

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

    def schedule_plugins(self, events):
        for name,plugin in self.plugins.items():
            logger.info("Scheduling plugin %s events", name)
            plugin.schedule(events)

    async def call_events(self, scenario, info_deploy):
        logger.info("Scheduling events")
                
        self.scenario = Scenario(None, None, None)
        self.scenario.parse(scenario)
        
        info_topology = info_deploy.get("topology")
        info_hosts = info_deploy.get("hosts")

        topo = self.scenario.get_topology()
        topo.fill_config(info_topology)
        topo.fill_hosts_config(info_hosts)
        self.topology = topo
        logger.debug("DOT: %s", self.topology.to_dot())
        self.config_plugins()

        events = scenario.get("events_fabric")
        self.schedule_plugins(events)

    def config_env_event(self, wflow_id):
        self.events_env.config(self.scenario.entrypoint.get("umbra-scenario"), wflow_id)
        self.plugins["environment"] = self.events_env

    async def call_env_event(self, wflow_id, scenario):
        logger.info("Scheduling environment events...")
        self.config_env_event(wflow_id)
        env_events = scenario.get("events_others").get("environment")

        # Any better way to get the id of event=current_topology?
        # Need it as the key to the 'result' dict which has
        # the response of the query for current topology
        curr_topo_id = None
        for event in env_events:
            if event["command"] == "current_topology":
                curr_topo_id = event["id"]

        result = await self.events_env.handle(env_events)

        # BUG: what if you have > 1 current_topology events? Above
        # `await` will block until you receive results from all tasks.
        # Correct behavior would be to straightaway update topology
        # after querying topology from umbra-scenario

        # update the topology with the newly received topology
        if curr_topo_id:
            topo = self.scenario.get_topology()
            updated_topo = result[curr_topo_id][1].get("topology")
            updated_host = result[curr_topo_id][1].get("hosts")
            topo.fill_config(updated_topo)
            topo.fill_hosts_config(updated_host)
            self.topology = topo
            logger.debug("DOT: %s", self.topology.to_dot())

        return result

    async def call_agent_event(self, scenario):
        logger.info("Scheduling agent events...")
        agent_events = scenario.get("events_others").get("agent")
        # '[0]' because we assume only single agent exist, thus all
        # events should have the same "agent_name"
        agent_name = agent_events[0].get("agent_name")

        # extract all the actions from agent_events to
        # construct the Instruction message
        agent_actions = []
        for ev in agent_events:
            for action in ev.get("actions"):
                agent_actions.append(action)

        instr_dict = {
            "id": scenario.get("id"),
            "actions": agent_actions
        }

        ip, port = self.agent_plugin[agent_name].split(':')
        channel = Channel(ip, int(port))
        stub = AgentStub(channel)

        instruction = json_format.ParseDict(instr_dict, Instruction())
        reply = await stub.Probe(instruction)
        channel.close()

    async def call_monitor_event(self, scenario):
        logger.info("Scheduling monitor events...")
        monitor_events = scenario.get("events_others").get("monitor")

        # extract all the actions from monitor_events to
        # construct the Instruction message
        monitor_actions = []
        for ev in monitor_events:
            for action in ev.get("actions"):
                monitor_actions.append(action)

        instr_dict = {
            "id": scenario.get("id"),
            "actions": monitor_actions
        }

        ip, port = self.scenario.entrypoint.get("umbra-monitor").split(':')
        channel = Channel(ip, int(port))
        stub = MonitorStub(channel)

        instruction = json_format.ParseDict(instr_dict, Instruction())
        reply = await stub.Listen(instruction)
        channel.close()

    async def run(self, request):
        logger.info("Running config request")
        report = Report(id=request.id)

        
        request_scenario = request.scenario
        # logger.debug(f"Received scenario: {request_scenario}")       
        scenario = self.parse_bytes(request_scenario)

        if scenario:
            topology = scenario.get("topology")
            address = scenario.get("entrypoint").get("umbra-scenario")
            ack,topo_info = await self.call_scenario(request.id, "start", topology, address)
            self.config_agent(topo_info, topology)

            if ack:
                events_info = await self.call_events(scenario, topo_info)

                status_info = {
                    'topology': topo_info,
                    'events': events_info,
                }
                status_bytes = self.serialize_bytes(status_info)
                report.status = status_bytes

                await asyncio.gather(
                    self.call_agent_event(scenario),
                    self.call_monitor_event(scenario),
                    self.call_env_event(request.id, scenario)
                )

            else:
                ack,topo_info = await self.call_scenario(request.id, "stop", {}, address)

        return report
