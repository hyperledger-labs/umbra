import logging
import json
import asyncio

from google.protobuf import json_format

from umbra.common.protobuf.umbra_grpc import MonitorBase
from umbra.common.protobuf.umbra_pb2 import Directrix, Status

from umbra.monitor.tools import Tools


logger = logging.getLogger(__name__)


class Monitor(MonitorBase):
    def __init__(self, info):
        self.info = info
        self.tools = Tools(info)

    async def Measure(self, stream):
        directrix: Directrix = await stream.recv_message()
        directrix_dict = json_format.MessageToDict(
            directrix, preserving_proto_field_name=True
        )
        status_dict = await self.tools.measure(directrix_dict)
        status = json_format.ParseDict(status_dict, Status())
        await stream.send_message(status)
