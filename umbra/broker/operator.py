import logging
import json
import asyncio
import functools
from datetime import datetime

from grpclib.client import Channel
from grpclib.exceptions import GRPCError

from google.protobuf import json_format

from umbra.common.protobuf.umbra_grpc import ScenarioStub
from umbra.common.protobuf.umbra_pb2 import Report, Workflow

from umbra.design.configs import Topology, Scenario
from umbra.broker.plugins.fabric import FabricEvents


logger = logging.getLogger(__name__)


class Operator:
    def __init__(self, info):
        self.info = info
        self.scenario = None
        self.topology = None
        self.events_fabric = FabricEvents()
        self.plugins = {}

    def parse_bytes(self, msg):
        msg_dict = {}

        if type(msg) is bytes:
            msg_str = msg.decode("utf32")
            msg_dict = json.loads(msg_str)

        return msg_dict

    def serialize_bytes(self, msg):
        msg_bytes = b""

        if type(msg) is dict:
            msg_str = json.dumps(msg)
            msg_bytes = msg_str.encode("utf32")

        return msg_bytes

    async def call_scenario(self, test, command, topology, address):
        logger.info(f"Deploying Scenario - {command}")

        scenario = self.serialize_bytes(topology)
        deploy = Workflow(id=test, workflow=command, scenario=scenario)
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

    async def call_events(self, scenario, info_deploy):
        logger.info("Scheduling events")

        self.scenario = Scenario("tmp")
        self.scenario.parse(scenario)

        info_topology = info_deploy.get("topology")
        info_hosts = info_deploy.get("hosts")

        topo = self.scenario.get_topology()
        topo.fill_config(info_topology)
        topo.fill_hosts_config(info_hosts)
        self.topology = topo
        self.config_plugins()

        events = scenario.get("events")
        self.schedule_plugins(events)

    async def call_scenarios(self, request, topology, mode):
        envs = topology.get_environments()
        topo_envs = topology.build_environments()

        logger.info(f"Environment scenarios - {envs}")
        logger.info(f"Environment topologies - {topo_envs}")

        acks = {}
        envs_topo_info = {}

        for env in topo_envs:
            if env in envs:
                env_data = envs.get(env)

                env_components = env_data.get("components")
                scenario_component = env_components.get("scenario")
                env_address = scenario_component.get("address")

                env_topo = topo_envs.get(env)

                ack, topo_info = await self.call_scenario(
                    request, mode, env_topo, env_address
                )

                acks[env] = ack
                envs_topo_info[env] = topo_info

        if all(acks.values()):
            logger.info(f"All environment scenarios deployed - {acks}")
        else:
            logger.info(f"Environment scenarios error - {acks}")

        return acks, envs_topo_info

    async def run(self, request):
        logger.info("Running scenario request")
        report = Report(id=request.id)

        request_scenario = request.scenario
        scenario = self.parse_bytes(request_scenario)

        if scenario:
            self.scenario = Scenario("tmp")
            self.scenario.parse(scenario)
            topology = self.scenario.get_topology()
            topology.build()

            acks, topos_info = await self.call_scenarios(request.id, topology, "start")

            if acks:
                # events_info = await self.call_events(scenario, topos_info)

                status_info = {
                    "topology": topos_info,
                    # "events": events_info,
                }
                status_bytes = self.serialize_bytes(status_info)
                report.status = status_bytes

            else:
                acks, topos_info = await self.call_scenarios(
                    request.id, topology, "stop"
                )
        return report
