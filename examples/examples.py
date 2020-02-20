import os
import sys
import json
import asyncio
import logging
import argparse
from datetime import datetime

from google.protobuf import json_format

from grpclib.client import Channel

from umbra.common.protobuf.umbra_grpc import BrokerStub
from umbra.common.protobuf.umbra_pb2 import Config, Report


logger = logging.getLogger(__name__)


class Examples:
    def __init__(self):
        self.cfg = None
        self.info = {}

    def parse(self, argv=None):
        logger.info(f"parsing argv: {argv}")
        parser = argparse.ArgumentParser(
            description='Umbra Examples App')

        parser.add_argument('--config',
                            type=str,
                            help='Define the test config file (default: None)')
        self.cfg, _ = parser.parse_known_args(argv)
        
        logger.info(f"args parsed: {self.cfg}")

        if self.cfg.config is not None:            
            return True   
        else:
            logger.info(f"Requested config {self.cfg.config} not available.")

        return False

    def filepath(self, name):
        filepath = os.path.normpath(os.path.join(
            os.path.dirname(__file__),
            name)
        )
        return filepath

    def load(self, filename):
        with open(filename, "+r") as fp:
            data = json.load(fp)
            return data

    async def call_config(self, stub):

        filename = self.cfg.config
        filepath = self.filepath(filename)

        config_dict = self.load(filepath)
        
        if config_dict:

            logger.info(f"Calling config {filename}")

            config_str = json.dumps(config_dict)
            config_bytes = config_str.encode('utf32')
            ts = datetime.now()

            # logger.debug(f"Message encoded: {config_bytes}")
            # config = {
            #     "id": filename,
            #     "scenario": config_bytes,
            #     "timestamp": ts.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            # }
            # config_msg = json_format.ParseDict(config, Config())

            config_msg = Config(id=filename, scenario=config_bytes)
            config_msg.timestamp.FromDatetime(datetime.now())

            reply = await stub.Run(config_msg)
            logger.info(f"Received Report {reply}")
      
    async def calls(self):
        logger.info(f"Calling: Broker Config")
        channel = Channel("172.17.0.1", 8989)
        stub = BrokerStub(channel)   
        await self.call_config(stub)
        channel.close()
       
    async def run(self, argv):
        ack = self.parse(argv)
        if ack:
            await self.calls()
            return 0
        else:
            return -1


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    argv = sys.argv[1:]
    examples = Examples()
    asyncio.run(examples.run(argv))