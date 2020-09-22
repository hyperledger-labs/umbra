import os
import json
import logging
import asyncio
import unittest

from umbra.scenario.main import Scenario
from umbra.design.configs import Scenario as DesignScenario

from utils import start_process, stop_process

logger = logging.getLogger(__name__)


LOCAL_FOLDER = os.path.abspath(os.path.dirname(__file__))
FIXTURES = "./fixtures"
FIXTURES_FOLDER = os.path.join(LOCAL_FOLDER, FIXTURES)


def parse_filename(filename):
    filepath = os.path.join(FIXTURES_FOLDER, filename)
    return filepath


def load_file(filename):
    try:
        filepath = parse_filename(filename)
        with open(filepath, "+r") as fp:
            json_dict = json.load(fp)
    except Exception as e:
        print(f"Could not load file {filename} - {e}")
        json_dict = {}

    finally:
        return json_dict


class TestScenario(unittest.TestCase):
    def test_scenario_start_stop(self):

        sc = Scenario("")

        scenario_config = load_file("./Fabric-Simple-01.json")

        scenario = DesignScenario("")
        ack = scenario.parse(scenario_config)

        assert ack is True

        topology = scenario.get_topology()
        topology.build()

        envs = topology.get_environments()
        topo_envs = topology.build_environments()

        logger.info(f"topology envs {envs}")

        topology_dict = topo_envs.get("env156")
        logger.info(json.dumps(topology_dict, sort_keys=True, indent=4))

        logger.info("Starting topology")
        reply = asyncio.run(sc.play("1", "start", topology_dict))
        ok, msg = reply

        logger.info(f"topology started {ok}")
        print(json.dumps(msg, sort_keys=True, indent=4))

        logger.info("Stopping topology")
        reply = asyncio.run(sc.play("1", "stop", topology_dict))
        ok, msg = reply

        logger.info(f"topology stoped {ok}")
        logger.info(json.dumps(msg, sort_keys=True, indent=4))


class TestUmbraScenario(unittest.TestCase):
    def start_component(self, uuid, address):
        command = "sudo umbra-scenario --uuid {uuid} --address {address} --debug &"
        cmd_formatted = command.format(uuid=uuid, address=address)
        cmd_args = cmd_formatted.split(" ")
        p = start_process(cmd_args)
        return p

    def stop_component(self, process):
        ack = stop_process(process)
        return ack

    def test_umbra_scenario(self):
        pass


if __name__ == "__main__":
    # logging.basicConfig(
    #     level=logging.DEBUG,
    #     format="%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s",
    # )
    # unittest.main()

    t = TestScenario()
    t.test_scenario_start_stop()
