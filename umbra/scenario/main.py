import asyncio
import logging
import signal
import time
import json
from multiprocessing import Process
from multiprocessing import Queue

from google.protobuf import json_format

from umbra.common.protobuf.umbra_grpc import ScenarioBase
from umbra.common.protobuf.umbra_pb2 import Workflow, Status

from umbra.scenario.environment import Environment


logger = logging.getLogger(__name__)


class Playground:
    def __init__(self, in_queue, out_queue):
        self.exp_topo = None

    def start(self, scenario):
        self.clear()
        self.exp_topo = Environment(scenario)
        ok, info = self.exp_topo.start()
        logger.info("hosts info %s", info)

        msg = {
            "info": info,
            "error": "",
        }

        ack = {
            "ok": str(ok),
            "msg": msg,
        }
        return ack

    def stop(self):
        logger.info("Stopping topo %s", self.exp_topo)

        ack = True
        if self.exp_topo:
            ack = self.exp_topo.stop()

        self.exp_topo = None

        msg = {
            "info": {},
            "error": "",
        }

        ack = {
            "ok": str(ack),
            "msg": msg,
        }
        return ack

    def stats(self):
        ok, info = "True", {}
        if self.exp_topo:
            ok, info = self.exp_topo.stats()

        ack = {
            "ok": str(ok),
            "msg": {
                "info": info,
                "error": "",
            },
        }

        return ack

    def update(self, scenario):
        ok, info = "True", {}
        if self.exp_topo:
            ok, info = self.exp_topo.update(scenario)

        ack = {
            "ok": str(ok),
            "msg": {
                "info": info,
                "error": "",
            },
        }

        return ack

    def clear(self):
        exp = Environment({})
        exp.mn_cleanup()
        logger.info("Experiments cleanup OK")


class Scenario(ScenarioBase):
    def __init__(self, info):
        self.info = info
        self.playground = Playground(None, None)

    async def play(self, id, action, scenario):
        if action == "start":
            reply = self.playground.start(scenario)

        elif action == "stop":
            reply = self.playground.stop()

        elif action == "update":
            reply = self.playground.update(scenario)

        elif action == "stats":
            reply = self.playground.stats()

        else:
            logger.debug(f"Unkown playground command {action}")
            return False, {}

        ack, info = reply.get("ok"), reply.get("msg")
        return ack, info

    def parse_bytes(self, msg):
        msg_dict = {}

        if type(msg) is bytes:
            msg_str = msg.decode("utf-8")
            msg_dict = json.loads(msg_str)

        return msg_dict

    def serialize_bytes(self, msg):
        msg_bytes = b""

        if type(msg) is dict:
            msg_str = json.dumps(msg)
            msg_bytes = msg_str.encode("utf-8")

        return msg_bytes

    async def Establish(self, stream):
        deploy = await stream.recv_message()

        scenario_bytes = deploy.scenario
        scenario = self.parse_bytes(scenario_bytes)

        deploy_dict = json_format.MessageToDict(
            deploy, preserving_proto_field_name=True
        )
        id = deploy_dict.get("id")
        action = deploy_dict.get("action")

        ok, msg = await self.play(id, action, scenario)
        logger.debug(f"Playground {ok} msg: {msg}")

        built_error = msg.get("error")
        built_info = self.serialize_bytes(msg.get("info"))

        built = Status(id=id, error=built_error, info=built_info)
        await stream.send_message(built)

    async def Stats(self, stream):
        wflow_raw = await stream.recv_message()
        scenario = self.parse_bytes(wflow_raw.scenario)

        wflow_dict = json_format.MessageToDict(
            wflow_raw, preserving_proto_field_name=True
        )
        ev_id = wflow_dict.get("id")
        command = wflow_dict.get("command")

        ok, msg = await self.play(id, command, scenario)
        logger.debug(f"command = {command}, Playground msg = {msg}")

        error = msg.get("error")
        topo_info = self.serialize_bytes(msg.get("info"))

        reply = Status(id=ev_id, ok=ok, error=error, info=topo_info)
        await stream.send_message(reply)