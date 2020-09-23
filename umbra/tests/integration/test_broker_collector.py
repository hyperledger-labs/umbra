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


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s",
    )

    unittest.main()
