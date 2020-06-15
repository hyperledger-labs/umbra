import sys
import json
import logging
import asyncio

# from umbra.common.protobuf.umbra_grpc import ScenarioBase
# from umbra.common.protobuf.umbra_pb2 import Deploy, Built

from umbra.agent.tools import Tools


logger = logging.getLogger(__name__)


class Agent():
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

    # async def Run(self, stream):
    #     deploy = await stream.recv_message()        
    #     scenario = self.parse_bytes(scenario_bytes)
        
    #     deploy_dict = json_format.MessageToDict(deploy, preserving_proto_field_name=True)

    #     logging.debug("Instruction Handled Ok -> Tools Workflow")
    #     self.tools.workflow(data)

    #     built_info = self.serialize_bytes(msg.get("info"))
    #     built = Built(id=id, ok=ok, error=error, info=built_info)
    #     await stream.send_message(built)
