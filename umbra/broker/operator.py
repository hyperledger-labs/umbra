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

from umbra.design.configs import Topology, Experiment
from umbra.broker.plugins.fabric import FabricEvents
from umbra.broker.plugins.env import EnvEventHandler

logger = logging.getLogger(__name__)

# port that umbra-agent binds to
AGENT_PORT = 8910


class Operator:
    def __init__(self, info):
        self.info = info
        self.experiment = None
        self.topology = None
        self.events_fabric = FabricEvents()
        self.events_env = EnvEventHandler()
        self.plugins = {}
        self.agent_plugin = {}

    def parse_bytes(self, msg):
        msg_dict = {}

        if type(msg) is bytes:
            msg_str = msg.decode("utf-8")
            if msg_str:
                msg_dict = json.loads(msg_str)

        return msg_dict

    def serialize_bytes(self, msg):
        msg_bytes = b""

        if type(msg) is dict:
            msg_str = json.dumps(msg)
            msg_bytes = msg_str.encode("utf-8")

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
            subdomain = hostname.split(".")[0]

            if subdomain in agents.keys():
                agent_ip = host_val.get("host_ip")
                self.agent_plugin[subdomain] = agent_ip + ":" + str(AGENT_PORT)
                logger.info(
                    "Added agent: agent_name = %s, at %s:%s",
                    subdomain,
                    agent_ip,
                    AGENT_PORT,
                )

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
            logger.info(f"Scenario not deployed error: {status.error}")
        else:
            ack = True
            logger.info(f"Scenario deployed: {status.ok}")

            info = self.parse_bytes(status.info)

        all_monitors_ack = all(all_acks.values())
        logger.info(f"Call monitors - action {action} - status: {all_monitors_ack}")
        return all_monitors_ack

    async def call_scenario(self, uid, action, topology, address):
        logger.info(f"Calling Experiment - {action}")

        scenario = self.serialize_bytes(topology)
        deploy = Workflow(id=uid, action=action, scenario=scenario)
        deploy.timestamp.FromDatetime(datetime.now())

        host, port = address.split(":")

        try:
            channel = Channel(host, port)
            stub = ScenarioStub(channel)
            status = await stub.Establish(deploy)

        except Exception as e:
            ack = False
            info = repr(e)
            logger.info(
                f"Error - deploy topology in environment failed - exceptio {info}"
            )
        else:
            if status.error:
                ack = False
                logger.info(f"Experiment not deployed error: {status.error}")
                info = status.error
            else:
                ack = True
                if status.info:
                    info = self.parse_bytes(status.info)
                else:
                    info = {}
                logger.info(f"Experiment info: {info}")
        finally:
            channel.close()

        return ack, info

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
            ack_fabric = self.events_fabric.config(
                topology, configsdk, chaincode, configtx
            )
            if ack_fabric:
                self.plugins["fabric"] = self.events_fabric

    def schedule_plugins(self, events):
        for name, plugin in self.plugins.items():
            logger.info("Scheduling plugin %s events", name)
            plugin.schedule(events)

    async def call_events(self, info_deploy):
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

        instr_dict = {"id": scenario.get("id"), "actions": agent_actions}

        ip, port = self.agent_plugin[agent_name].split(":")
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

        instr_dict = {"id": scenario.get("id"), "actions": monitor_actions}

        ip, port = self.scenario.entrypoint.get("umbra-monitor").split(":")
        channel = Channel(ip, int(port))
        stub = MonitorStub(channel)

        instruction = json_format.ParseDict(instr_dict, Instruction())
        reply = await stub.Listen(instruction)
        channel.close()

    async def run(self, request):
        logger.info("Running config request")
        report = Report(id=request.id)

        logger.info(f"Calling scenarios - {action}")
        logger.info(f"Environment scenarios - {envs}")
        logger.debug(f"Environment topologies - {topo_envs}")

        if scenario:
            topology = scenario.get("topology")
            address = scenario.get("entrypoint").get("umbra-scenario")
            ack, topo_info = await self.call_scenario(
                request.id, "start", topology, address
            )
            self.config_agent(topo_info, topology)

            if ack:
                events_info = await self.call_events(scenario, topo_info)

                env_components = env_data.get("components")
                scenario_component = env_components.get("scenario")
                env_address = scenario_component.get("address")

                env_topo = topo_envs.get(env)

                ack, topo_info = await self.call_scenario(
                    uid, action, env_topo, env_address
                )

                acks[env] = ack
                envs_topo_info[env] = topo_info

        if all(acks.values()):
            logger.info(f"All environment scenarios deployed - {acks}")
        else:
            logger.info(f"Environment scenarios error - {acks}")

        return acks, envs_topo_info

    def load(self, scenario_message):
        try:
            scenario = self.parse_bytes(scenario_message)
            self.experiment = Experiment("tmp")
            self.experiment.parse(scenario)
            topology = self.experiment.get_topology()
            topology.build()
            self.topology = topology
            ack = True
        except Exception as e:
            logger.info(f"Could not load scenario - exception {repr(e)}")
            ack = False
        finally:
            return ack

    async def start(self, uid):
        topology = self.experiment.get_topology()
        acks, stats = await self.call_scenarios(uid, topology, "start")

        info, error = {}, {}
        if all(acks.values()):
            all_monitors_ack = await self.call_monitors(stats, "start")
            info = stats
        else:
            error = stats

        return info, error

    async def stop(self, uid):
        topology = self.experiment.get_topology()

        acks, stats = await self.call_scenarios(uid, topology, "stop")

        info, error = {}, {}
        if all(acks.values()):
            all_monitors_ack = await self.call_monitors(stats, "stop")
            info = stats
        else:
            error = stats

        return info, error

    def build_report(self, uid, info, error):
        info_msg = self.serialize_bytes(info)
        error_msg = self.serialize_bytes(error)
        report = Report(id=uid, info=info_msg, error=error_msg)
        return report

    async def execute(self, config):
        uid = config.id
        action = config.action
        scenario = config.scenario

        if self.load(scenario):

            info, error = {}, {}

            if action == "start":
                info, error = await self.start(uid)

                if not error:
                    events_info = await self.call_events(info)

            elif action == "stop":
                info, error = await self.stop(uid)

                await asyncio.gather(
                    self.call_agent_event(scenario),
                    self.call_monitor_event(scenario),
                    self.call_env_event(request.id, scenario),
                )

            else:
                error = {
                    "Execution error": f"Unkown action ({action}) to execute config"
                }

            report = self.build_report(uid, info, error)

        else:
            error_msg = "scenario could not be parsed/loaded"
            report = Report(id=config.id, error=error_msg)

        return report
