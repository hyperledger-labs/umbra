import sys
import json
import asyncio
import logging
from datetime import datetime
from google.protobuf import json_format
from grpclib.client import Channel

from umbra.common.protobuf.umbra_grpc import BrokerStub
from umbra.common.protobuf.umbra_pb2 import Config, Report

from umbra.common.protobuf.umbra_grpc import BrokerStub


logger = logging.getLogger(__name__)


class UmbraInterface:
    def __init__(self):
        pass


class BrokerInterface(UmbraInterface):
    def __init__(self):
        UmbraInterface.__init__(self)

    async def call_config(self, stub, topology_cfg):
        topology_cfg_id = topology_cfg.get("id")
        config_str = json.dumps(topology_cfg)
        config_bytes = config_str.encode("utf32")

        config_msg = Config(id=topology_cfg_id, scenario=config_bytes)
        config_msg.timestamp.FromDatetime(datetime.now())

        reply = await stub.Manage(config_msg)
        reply_dict = json_format.MessageToDict(reply)
        logger.info(f"Received Report {reply_dict}")

        return reply_dict

    async def calls(self, address, topology_cfg, action):
        logger.info(f"Calling Broker")
        ip, port = address.split(":")
        channel = Channel(ip, port)
        stub = BrokerStub(channel)
        reply_dict = await self.call_config(stub, topology_cfg)
        channel.close()
        return reply_dict
