import logging
import json
import asyncio

from google.protobuf import json_format

from umbra.common.protobuf.umbra_grpc import MonitorBase
from umbra.common.protobuf.umbra_pb2 import Instruction, Evaluation

from umbra.monitor.tools import Tools


logger = logging.getLogger(__name__)


class Monitor(MonitorBase):
    def __init__(self):
        self.tools = Tools()
      
    def parse_bytes(self, msg):
        msg_dict = {}

        if type(msg) is bytes:
            msg_str = msg.decode('utf32')
            msg_dict = json.loads(msg_str)
        
        return msg_dict

    def serialize_bytes(self, msg):
        msg_bytes = b''

        if type(msg) is dict:
            msg_str = json.dumps(msg)
            msg_bytes = msg_str.encode('utf32')
            
        return msg_bytes

    async def Listen(self, stream):
        instruction: Instruction = await stream.recv_message()        
        instruction_dict = json_format.MessageToDict(instruction, preserving_proto_field_name=True)

        logging.debug("Instruction Handled -> Tools Workflow")
        evaluation_dict = await self.tools.workflow(instruction_dict)

        evaluation = Evaluation()
        
        await stream.send_message(evaluation)
