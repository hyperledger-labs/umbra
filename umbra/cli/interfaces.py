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

    def load(self, filename):
        with open(filename, "+r") as fp:
            data = json.load(fp)
            return data

    async def call_config(self, filepath, stub):

        config_dict = self.load(filepath)

        if config_dict:

            logger.info(f"Calling config {filepath}")

            config_str = json.dumps(config_dict)
            config_bytes = config_str.encode("utf32")
            # ts = datetime.now()
            # logger.debug(f"Message encoded: {config_bytes}")
            # config = {
            #     "id": filename,
            #     "scenario": config_bytes,
            #     "timestamp": ts.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            # }
            # config_msg = json_format.ParseDict(config, Config())

            config_msg = Config(id=filepath, scenario=config_bytes)
            config_msg.timestamp.FromDatetime(datetime.now())

            reply = await stub.Manage(config_msg)
            logger.info(f"Received Report {reply}")

    async def calls(self, filepath):
        logger.info(f"Calling: Broker Config")
        channel = Channel("172.17.0.1", 8989)
        stub = BrokerStub(channel)
        await self.call_config(filepath, stub)
        channel.close()
