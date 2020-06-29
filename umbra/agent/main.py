import logging
import json
import asyncio

from google.protobuf import json_format

from umbra.common.protobuf.umbra_grpc import AgentBase
from umbra.common.protobuf.umbra_pb2 import Instruction, Evaluation

from umbra.agent.tools import Tools


logger = logging.getLogger(__name__)


class Agent(AgentBase):
    def __init__(self):
        self.tools = Tools()
      
    async def Probe(self, stream):
        logging.debug("Instruction Received")
        instruction: Instruction = await stream.recv_message()        
        instruction_dict = json_format.MessageToDict(instruction, preserving_proto_field_name=True)
        evaluation_dict = await self.tools.handle(instruction_dict)
        evaluation = json_format.ParseDict(evaluation_dict, Evaluation())
        await stream.send_message(evaluation)
