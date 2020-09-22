import logging
import json
import asyncio
import functools
from datetime import datetime

from grpclib.client import Channel
from grpclib.exceptions import GRPCError

from google.protobuf import json_format

from umbra.common.protobuf.umbra_grpc import ScenarioStub, MonitorStub
from umbra.common.protobuf.umbra_pb2 import Report, Workflow, Directrix, Status

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

    async def call_monitor(self, address, data):
        logger.info(f"Calling Monitor - {address}")

        directrix = json_format.ParseDict(data, Directrix())
        host, port = address.split(":")

        try:
            channel = Channel(host, port)
            stub = MonitorStub(channel)
            status = await stub.Measure(directrix)

        except Exception as e:
            ack = False
            info = repr(e)
            logger.info(f"Error - monitor failed - {info}")
        else:
            if status.error:
                ack = False
                logger.info(f"Monitor error: {status.error}")
                info = status.error
            else:
                ack = True
                if status.info:
                    info = self.parse_bytes(status.info)
                else:
                    info = {}
                logger.info(f"Monitor info: {info}")
        finally:
            channel.close()

        return ack, info

    def get_monitor_env_address(self, env):
        envs = self.topology.get_environments()
        env_data = envs.get(env)
        env_components = env_data.get("components")
        env_monitor_component = env_components.get("monitor")
        env_monitor_address = env_monitor_component.get("address")
        return env_monitor_address

    def build_monitor_directrix(self, env, info, action):
        hosts = info.get("topology").get("hosts")
        targets = repr(set(hosts.keys()))

        data = {
            "action": action,
            "flush": {
                "live": True,
                "environment": env,
                "address": self.info.get("address"),
            },
            "sources": [
                {
                    "id": 1,
                    "name": "container",
                    "parameters": {
                        "targets": targets,
                        "duration": "30",
                        "interval": "5",
                    },
                    "schedule": {},
                },
                {
                    "id": 2,
                    "name": "host",
                    "parameters": {
                        "duration": "30",
                        "interval": "5",
                    },
                    "schedule": {},
                },
            ],
        }

        return data

    async def call_monitors(self, stats, action):
        logger.info(f"Call monitors")

        all_acks = {}
        for env, info in stats.items():
            data = self.build_monitor_directrix(env, info, action)
            address = self.get_monitor_env_address(env)
            ack, info = await self.call_monitor(address, data)
            all_acks[env] = ack

        all_monitors_ack = all(all_acks.values())
        logger.info(f"Call monitors - action {action} - status: {all_monitors_ack}")
        return all_monitors_ack

    async def call_scenario(self, uid, action, topology, address):
        logger.info(f"Calling Scenario - {action}")

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
                logger.info(f"Scenario not deployed error: {status.error}")
                info = status.error
            else:
                ack = True
                if status.info:
                    info = self.parse_bytes(status.info)
                else:
                    info = {}
                logger.info(f"Scenario info: {info}")
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

    async def call_scenarios(self, uid, topology, action):
        envs = topology.get_environments()
        topo_envs = topology.build_environments()

        logger.info(f"Calling scenarios - {action}")
        logger.info(f"Environment scenarios - {envs}")
        logger.debug(f"Environment topologies - {topo_envs}")

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
            self.scenario = Scenario("tmp")
            self.scenario.parse(scenario)
            topology = self.scenario.get_topology()
            topology.build()
            self.topology = topology
            ack = True
        except Exception as e:
            logger.info(f"Could not load scenario - exception {repr(e)}")
            ack = False
        finally:
            return ack

    async def start(self, uid):
        topology = self.scenario.get_topology()
        acks, stats = await self.call_scenarios(uid, topology, "start")

        info, error = {}, {}
        if all(acks.values()):
            all_monitors_ack = await self.call_monitors(stats, "start")
            info = stats
        else:
            error = stats

        return info, error

    async def stop(self, uid):
        topology = self.scenario.get_topology()

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

                # events_info = await self.call_events()

            elif action == "stop":
                info, error = await self.stop(uid)

            else:
                error = {
                    "Execution error": f"Unkown action ({action}) to execute config"
                }

            report = self.build_report(uid, info, error)

        else:
            error_msg = "scenario could not be parsed/loaded"
            report = Report(id=config.id, error=error_msg)

        return report
