import logging
import unittest
import asyncio
from google.protobuf import json_format

from umbra.common.protobuf.umbra_pb2 import Instruction, Snapshot

from umbra.monitor.tools import Tools


logger = logging.getLogger(__name__)


actions = [
    {
        "id": "2",
        "tool": "host",
        "output": {"live": False, "address": None,},
        "parameters": {"interval": "1", "duration": "3",},
        "schedule": {"from": 0, "until": 14, "duration": 0, "interval": 2, "repeat": 2},
    },
    {
        "id": "3",
        "tool": "container",
        "output": {"live": False, "address": None,},
        "parameters": {"interval": "1", "duration": "3", "target": "ivan",},
        "schedule": {
            "from": 5,
            "until": 10,
            "duration": 10,
            "interval": 0,
            "repeat": 0,
        },
    },
]


class TestMonitor(unittest.TestCase):
    def test_dummy_tool(self):

        actions = [
            {
                "id": "3",
                "tool": "dummy",
                "output": {"live": False, "address": None,},
                "parameters": {"interval": "1", "duration": "3",},
                "schedule": {},
            },
        ]

        inst_dict = {
            "id": "100",
            "actions": actions,
        }

        tools = Tools()
        out = asyncio.run(tools.handle(inst_dict))
        print(out)

    def test_tools(self):
        actions = [
            {
                "id": "1",
                "tool": "process",
                "output": {"live": False, "address": None,},
                "parameters": {"pid": "2417", "interval": "1", "duration": "3",},
                "schedule": {},
            },
            {
                "id": "2",
                "tool": "container",
                "output": {"live": False, "address": None,},
                "parameters": {"target": "teste", "interval": "1", "duration": "3",},
                "schedule": {},
            },
            {
                "id": "3",
                "tool": "host",
                "output": {"live": False, "address": None,},
                "parameters": {"interval": "1", "duration": "3",},
                "schedule": {},
            },
            {
                "id": "4",
                "tool": "tcpdump",
                "output": {"live": False, "address": None,},
                "parameters": {"interface": "wlp82s0", "pcap": "wlp82s0.pcap"},
                "schedule": {"duration": 3,},
            },
        ]

        inst_dict = {
            "id": "100",
            "actions": actions,
        }

        # tools = Tools()
        # out = asyncio.run(tools.handle(inst_dict))
        # print(out)

        tools = Tools()
        instruction = json_format.ParseDict(inst_dict, Instruction())
        instruction_dict = json_format.MessageToDict(
            instruction, preserving_proto_field_name=True
        )
        snapshot_dict = asyncio.run(tools.handle(instruction_dict))
        # snapshot = json_format.ParseDict(snapshot_dict, Snapshot())
        print(snapshot_dict)


def main():
    t = TestMonitor()
    # t.test_dummy_tool()
    t.test_tools()


if __name__ == "__main__":
    # unittest.main()
    logging.basicConfig(level=logging.DEBUG)
    main()
