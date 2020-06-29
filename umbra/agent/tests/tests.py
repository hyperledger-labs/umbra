import logging
import unittest
import asyncio
from google.protobuf import json_format

from umbra.common.protobuf.umbra_pb2 import Instruction

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
        # {
        #     'id': "1",
        #     "tool": "ping",
        #     "output": {
        #         "live": False,
        #         "address": None,
        #     },
        #     'parameters': {
        #         "target": "127.0.0.1",
        #         "interval": "1",
        #         "duration": "3",
        #     },
        #     'schedule': {}
        # },
        # {
        #     'id': "2",
        #     "tool": "iperf3",
        #     "output": {
        #         "live": False,
        #         "address": None,
        #     },
        #     'parameters': {
        #         'port': "9030",
        #         'duration': "2",
        #         'client': "True",
        #         'server': '127.0.0.1',
        #     },
        #     'schedule': {}
        # },
        {
            'id': "3",
            "tool": "tcpreplay",
            "output": {
                "live": False,
                "address": None,
            },
            'parameters': {
                'interface': 'lo',
                'duration': "5",
                'pcap': 'wlp82s0.pcap',
            },
            'schedule': {}
        },
        ]

        inst_dict = {
            "id": "100",
            "actions": actions,
        }
                
        tools = Tools()
        out = asyncio.run(tools.handle(inst_dict))
        print(out)


def main():
    t = TestMonitor()
    # t.test_dummy_tool()
    t.test_tools()


if __name__ == "__main__":
    # unittest.main()
    logging.basicConfig(level=logging.DEBUG)
    main()
