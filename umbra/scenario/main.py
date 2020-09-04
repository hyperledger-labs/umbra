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
        self.in_queue = in_queue
        self.out_queue = out_queue
        self.init()

    def init(self):
        self.loop(self.in_queue, self.out_queue)

    def loop(self, in_queue, out_queue):
        logger.info("Playground loop started")
        while True:
            try:
                msg = in_queue.get()
            except Exception as e:
                logger.debug(f"Exception in the loop: {e}")
            else:
                cmd = msg.get("cmd")
                scenario = msg.get("scenario")

                logger.info("Playground command %s", cmd)

                if cmd == "start":
                    reply = self.start(scenario)
                elif cmd == "stop":
                    reply = self.stop()
                else:
                    reply = {}

                out_queue.put(reply)

                if cmd == "stop":
                    break

    def start(self, scenario):
        self.clear()
        self.exp_topo = Environment(scenario)
        ok, info = self.exp_topo.start()
        logger.info("hosts info %s", info)

        msg = {
            "info": info,
            "error": None,
        }

        ack = {
            "ok": str(ok),
            "msg": msg,
        }
        return ack

    def stop(self):
        logger.info("Stopping topo %s", self.exp_topo)
        ack = self.exp_topo.stop()
        self.exp_topo = None

        msg = {
            "info": "",
            "error": "",
        }

        ack = {
            "ok": str(ack),
            "msg": msg,
        }
        return ack

    def clear(self):
        exp = Environment({})
        exp.mn_cleanup()
        logger.info("Experiments cleanup OK")


class Scenario(ScenarioBase):
    def __init__(self):
        self.playground = None
        self.in_queue = Queue()
        self.out_queue = Queue()

    async def call(self, cmd, scenario):
        msg = {"cmd": cmd, "scenario": scenario}
        self.in_queue.put(msg)
        reply = self.out_queue.get()
        return reply

    def init(self):
        Playground(self.in_queue, self.out_queue)
        print("Finished Playground")

    def start(self):
        self.in_queue = Queue()
        self.out_queue = Queue()
        self.playground = Process(target=self.init)
        self.playground.start()
        logger.info("Started playground")

    def stop(self):
        self.playground.join(1)
        time.sleep(0.5)
        logger.info("playground alive %s", self.playground.is_alive())
        logger.info("playground exitcode ok %s", self.playground.exitcode)
        self.in_queue = None
        self.out_queue = None
        self.playground = None
        logger.info("Stoped playground")

    async def play(self, id, command, scenario):
        if command == "start":
            if self.playground:
                logger.debug("Stopping running playground")
                await self.call("stop", None)
                self.stop()

            self.start()
            reply = await self.call(command, scenario)

        elif command == "stop":
            reply = await self.call(command, scenario)
            self.stop()
        else:
            logger.debug(f"Unkown playground command {command}")
            return False, {}

        ack, info = reply.get("ok"), reply.get("msg")
        return ack, info

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
        logger.debug(f"Playground msg: {msg}")

        error = msg.get("error")
        built_info = self.serialize_bytes(msg.get("info"))

        built = Status(id=id, ok=ok, error=error, info=built_info)
        await stream.send_message(built)
