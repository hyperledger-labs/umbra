import unittest
import logging
import json
import os
from datetime import datetime

from google.protobuf import json_format

from umbra.common.protobuf.umbra_pb2 import Config
from umbra.design.configs import Topology, Scenario


class TestScenario(unittest.TestCase):
    def parse_bytes(self, msg):
        msg_dict = {}

        if type(msg) is bytes:
            msg_str = msg.decode("utf32")
            msg_dict = json.loads(msg_str)

        return msg_dict

    def filepath(self, name):
        filepath = os.path.normpath(os.path.join(os.path.dirname(__file__), name))
        return filepath

    def load(self, filename):
        with open(filename, "+r") as fp:
            data = json.load(fp)
            return data

    def test_scenario_parse(self):
        filename = "./fixtures/Fabric-Simple-01.json"
        filepath = self.filepath(filename)
        config_dict = self.load(filepath)

        config_str = json.dumps(config_dict)
        config_bytes = config_str.encode("utf32")
        config_msg = Config(id=filename, scenario=config_bytes)
        config_msg.timestamp.FromDatetime(datetime.now())

        request_scenario = config_msg.scenario
        scenario_dict = self.parse_bytes(request_scenario)

        scenario = Scenario("tmp")
        scenario.parse(scenario_dict)
        topology = scenario.get_topology()
        topology.show()

        topo_envs = topology.build_environments()
        print(topo_envs)

        envs = topology.get_environments()
        print(envs)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
