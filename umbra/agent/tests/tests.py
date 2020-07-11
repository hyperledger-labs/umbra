import logging
import unittest
import asyncio
from google.protobuf import json_format

from umbra.common.protobuf.umbra_pb2 import Instruction, Snapshot

from umbra.agent.tools import Tools


logger = logging.getLogger(__name__)


        # 'schedule': {
        #     "from": 0,
        #     "until": 14,
        #     "duration": 0,
        #     "interval": 2,
        #     "repeat": 2
        # },

class TestMonitor(unittest.TestCase):


    def test_tools(self):
        actions = [
        {
            'id': "1",
            "tool": "ping",
            "output": {
                "live": False,
                "address": None,
            },
            'parameters': {
                "target": "127.0.0.1",
                "interval": "1",
                "duration": "3",
            },
            'schedule': {
                "from": 0,
                "until": 14,
                "duration": 0,
                "interval": 2,
                "repeat": 2
            },
        },
        # {
        #     'id': "2",
        #     "tool": "iperf3",
        #     "output": {
        #         "live": False,
        #         "address": None,
        #     },
        #     'parameters': {
        #         'port': "9030",
        #         'duration': "3",
        #         'client': "True",
        #         'server': '127.0.0.1',
        #     },
        #     'schedule': {}
        # },
        # {
        #     'id': "3",
        #     "tool": "tcpreplay",
        #     "output": {
        #         "live": False,
        #         "address": None,
        #     },
        #     'parameters': {
        #         'interface': 'lo',
        #         'duration': "5",
        #         'folder': "/tmp/",
        #         'pcap': 'wlp82s0.pcap',
        #     },
        #     'schedule': {}
        # },
        ]

        inst_dict = {
            "id": "100",
            "actions": actions,
        }
        
        
        tools = Tools()
        instruction = json_format.ParseDict(inst_dict, Instruction())
        instruction_dict = json_format.MessageToDict(instruction, preserving_proto_field_name=True)
        snapshot_dict = asyncio.run(tools.handle(instruction_dict))
        snapshot = json_format.ParseDict(snapshot_dict, Snapshot())
        print(snapshot)


# def main():
#     t = TestMonitor()
#     t.test_tools()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    unittest.main()
    # main()