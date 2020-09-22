import json
import asyncio
import logging

from umbra.common.protobuf.umbra_grpc import BrokerBase
from umbra.broker.operator import Operator
from umbra.broker.collector import Collector


logger = logging.getLogger(__name__)


class Broker(BrokerBase):
    def __init__(self, info):
        self.info = info
        self.operator = Operator(info)
        self.collector = Collector(info)

    async def Execute(self, stream):
        request = await stream.recv_message()
        reply = await self.operator.execute(request)
        await stream.send_message(reply)

    async def Collect(self, stream):
        request = await stream.recv_message()
        reply = await self.collector.collect(request)
        await stream.send_message(reply)
