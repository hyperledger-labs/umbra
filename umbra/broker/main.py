import json
import asyncio
import logging

from umbra.common.protobuf.umbra_grpc import BrokerBase
from umbra.broker.operator import Operator
from umbra.broker.collector import Collector


logger = logging.getLogger(__name__)
logging.getLogger("hpack").setLevel(logging.WARNING)


class Broker(BrokerBase):
    def __init__(self, info):
        self.info = info
        self.operator = Operator(info)
<<<<<<< HEAD
        self.collector = Collector(info)

    async def Execute(self, stream):
        request = await stream.recv_message()
        reply = await self.operator.execute(request)
        await stream.send_message(reply)

    async def Collect(self, stream):
||||||| 3052fe4
    
    async def Run(self, stream):
=======
    
    async def Manage(self, stream):
>>>>>>> 091d3a4f7e95c782e110b79ee0a83fd1d49c8a00
        request = await stream.recv_message()
<<<<<<< HEAD
        reply = await self.collector.collect(request)
        await stream.send_message(reply)
||||||| 3052fe4
        reply = await self.operator.run(request)
        await stream.send_message(reply)
=======
        reply = await self.operator.run(request)
        await stream.send_message(reply)

    async def Measure(self, stream):
        request = await stream.recv_message()
        reply = await self.operator.run(request)
        await stream.send_message(reply)
>>>>>>> 091d3a4f7e95c782e110b79ee0a83fd1d49c8a00
