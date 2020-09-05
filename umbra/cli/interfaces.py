import sys
import json
import asyncio
import logging
from datetime import datetime
from google.protobuf import json_format
from grpclib.client import Channel
from grpclib.exceptions import GRPCError

from umbra.common.protobuf.umbra_grpc import BrokerStub
from umbra.common.protobuf.umbra_pb2 import Config, Report

from umbra.common.protobuf.umbra_grpc import BrokerStub


logger = logging.getLogger(__name__)


class UmbraInterface:
    def __init__(self):
        pass

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

    async def call_stub(self, stub_func, msg):
        reply, error = {}, ""
        try:
            msg_reply = await stub_func(msg)
            reply = json_format.MessageToDict(
                msg_reply, preserving_proto_field_name=True
            )

        except GRPCError as e:
            error = f"Could not reach stub grpcerror - exception {repr(e)} "
            logger.debug(f"Exception: {error}")

        except OSError as e:
            error = f"Could not reach stub channel - exception {repr(e)} "
            logger.debug(f"Exception: {error}")

        finally:
            return reply, error


class BrokerInterface(UmbraInterface):
    def __init__(self):
        UmbraInterface.__init__(self)

    async def call(self, address, action, scenario):
        uid = scenario.get("name", "")
        scenario_msg = self.serialize_bytes(scenario)
        config_msg = Config(id=uid, action=action, scenario=scenario_msg)
        config_msg.timestamp.FromDatetime(datetime.now())

        ip, port = address.split(":")
        channel = Channel(ip, port)
        stub = BrokerStub(channel)

        reply, error = await self.call_stub(stub.Execute, config_msg)

        channel.close()
        return reply, error

    def begin(self, environment, topology):
        address = environment.get("address")
        action = "start"
        reply, error = asyncio.run(self.call(address, action, topology))
        return reply, error

    def end(self, environment, topology):
        address = environment.get("address")
        action = "stop"
        reply, error = asyncio.run(self.call(address, action, topology))
        return reply, error

