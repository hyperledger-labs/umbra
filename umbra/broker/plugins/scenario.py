import logging
import json
from datetime import datetime
from grpclib.client import Channel

from umbra.common.protobuf.umbra_grpc import ScenarioStub
from umbra.common.protobuf.umbra_pb2 import Report, Workflow


logger = logging.getLogger(__name__)


class ScenarioEvents:
    """
    Responsible for handling environment related events.
    It will construct EnvEvent class based on user-defined events
    and schedule it to run using umbra/common/scheduler component
    """

    def __init__(self):
        self.topo = None
        self.envs = None

    def config(self, topo):
        logger.info("Configuring scenario plugin")
        self.topo = topo
        self.envs = self.topo.get_environments()

    def get_event_environment(self, event):
        event_group = event.get("group")
        event_target = event.get("target")

        env = None

        if event_group == "links":
            src = event_target[0]
            dst = event_target[1]

            if self.topo.has("node", src) and self.topo.has("node", dst):
                node_data = self.topo.get_data("node", src)
                env = node_data.get("environment", None)
            else:
                logger.info(f"Scenario event link {event_target} not found in topology")

        if event_group == "nodes":
            if self.topo.has("node", event_target):
                node_data = self.topo.get_data("node", event_target)
                env = node_data.get("environment", None)
            else:
                logger.info(f"Scenario event node {event_target} not found in topology")

        return env

    def get_event_scenario_address(self, event):
        env = self.get_event_environment(event)

        if env:
            env_data = self.envs.get(env)
            env_components = env_data.get("components")
            scenario_component = env_components.get("scenario")
            env_address = scenario_component.get("address")
            return env_address

        return None

    def schedule(self, events):
        evs_sched = {}

        for event in events:
            ev_id = event.get("id")
            ev_data = event.get("event")
            address = self.get_event_scenario_address(ev_data)

            if address:
                logger.info(f"Scheduling scenario event {event} to address {address}")
                action_call = self.call_scenario(address, event)
                evs_sched[ev_id] = (action_call, event.get("schedule"))
            else:
                logger.info(
                    f"Could not schedule scenario event - environment address not found for {event}"
                )

        return evs_sched

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

    async def call_scenario(self, address, event):
        ev_id = event.get("id")
        ev_data = event.get("event")

        logger.debug(f"Event scenario: {ev_data}")
        logger.debug(f"Event scenario to: {address}")
        
        try:
            event_bytes = self.serialize_bytes(ev_data)
            deploy = Workflow(id=str(ev_id), action="update", scenario=event_bytes)       
            deploy.timestamp.FromDatetime(datetime.now())
            
            host, port = address.split(":")
            channel = Channel(host, port)
            stub = ScenarioStub(channel)
            status = await stub.Establish(deploy)
        except Exception as e:
            ack = False
            info = repr(e)
            logger.info(
                f"Error - event scenario failed - exceptio {info}"
            )
        else:
            if status.error:
                ack = False
                logger.info(f"Event scenario error: {status.error}")
                info = status.error
            else:
                ack = True
                if status.info:
                    info = self.parse_bytes(status.info)
                else:
                    info = {}
                logger.info(f"Event scenario ok: {info}")
        finally:
            channel.close()

        return ack, info
