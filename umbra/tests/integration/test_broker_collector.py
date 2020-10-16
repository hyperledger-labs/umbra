import logging
import json
import unittest
import asyncio


from umbra.broker.collector import GraphanaInterface


logger = logging.getLogger(__name__)


class TestBrokerCollector(unittest.TestCase):
    async def create_datasource(self):
        gi = GraphanaInterface()

        info = {
            "address": "172.17.0.1",
            "database": "y",
        }

        await gi.add_datasource(info)

    async def get_datasources(self):
        gi = GraphanaInterface()

        info = {
            "address": "172.17.0.1",
        }

        reply = await gi.get_datasources(info)
        return reply

    def test_datasource(self):
        asyncio.run(self.create_datasource())
        reply = asyncio.run(self.get_datasources())

        ok = False
        for ds in reply:
            db = ds.get("database", None)

            if db == "y":
                ok = True

        assert ok is True

    async def create_dashboard(self):
        gi = GraphanaInterface()

        info = {
            "address": "172.17.0.1",
            "database": "y",
        }

        await gi.add_dashboard(info)

        info = {
            "address": "172.17.0.1",
            "database": "x",
        }

        await gi.add_dashboard(info)

    async def get_dashboard(self):
        gi = GraphanaInterface()

        info = {
            "address": "172.17.0.1",
        }

        reply = await gi.get_dashboard(info)
        return reply

    def test_dashboard(self):
        asyncio.run(self.create_dashboard())
        reply = asyncio.run(self.get_dashboard())

        ok = False

        if reply.get("dashboard", None):
            dashboard = reply.get("dashboard")
            dash_uid = dashboard.get("uid")

            if dash_uid == "umbra":
                ok = True

        assert ok is True


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s",
    )
    suite = unittest.TestSuite()
    suite.addTest(TestBrokerCollector("test_dashboard"))
    runner = unittest.TextTestRunner()
    runner.run(suite)

    # unittest.main()
