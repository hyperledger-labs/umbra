import logging
import json
import unittest
import asyncio


from umbra.broker.plugins.scenario import ScenarioEvents
from umbra.common.scheduler import Handler


class TestScenarioEvents(unittest.TestCase):

    def test_call(self):

        address = "localhost:8957"
        ev_scenario = {
            "group": "nodes",
            "specs": {
                "action": "update",
                "online": False,
                "resources": {},
            },
            "target": "peer0.org1.example.com",
        }

        sched_ev = {"from": 2}


        sc_ev = ScenarioEvents()

        event = {
            "id": 1,
            "event": ev_scenario,
        }
        reply = asyncio.run(sc_ev.call_scenario(address, event))

        

    def test_handler_call(self):
        address = "localhost:8957"
        ev_scenario = {
            "group": "nodes",
            "specs": {
                "action": "update",
                "online": False,
                "resources": {},
            },
            "target": "peer0.org1.example.com",
        }

        sched_ev = {"from": 2}

        event = {
            "id": 1,
            "event": ev_scenario,
        }
        sc_ev = ScenarioEvents()

        evs_sched = {}
        action_call = sc_ev.call_scenario(address, event)
        evs_sched[1] = (action_call, sched_ev)

        
        
        handler = Handler()
        ack = asyncio.run(handler.run(evs_sched))
        print(ack)


logger = logging.getLogger(__name__)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s",
    )
    suite = unittest.TestSuite()
    # suite.addTest(TestScenarioEvents("test_call"))
    suite.addTest(TestScenarioEvents("test_handler_call"))
    runner = unittest.TextTestRunner()
    runner.run(suite)

    # unittest.main()
