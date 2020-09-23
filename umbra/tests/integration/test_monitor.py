import logging
import json
import unittest
import asyncio
from grpclib.client import Channel
from google.protobuf import json_format

from umbra.common.protobuf.umbra_grpc import MonitorStub
from umbra.common.protobuf.umbra_pb2 import Directrix, Status


from utils import start_process, stop_process

logger = logging.getLogger(__name__)


class TestMonitor(unittest.TestCase):
    def start_broker(self, uuid, address):
        command = "umbra-broker --uuid {uuid} --address {address} --debug &"
        cmd_formatted = command.format(uuid=uuid, address=address)
        cmd_args = cmd_formatted.split(" ")
        p = start_process(cmd_args)
        return p

    def stop_broker(self, broker_process):
        ack = stop_process(broker_process)
        return ack

    def start_monitor(self, uuid, address):
        command = "umbra-monitor --uuid {uuid} --address {address} --debug &"
        cmd_formatted = command.format(uuid=uuid, address=address)
        cmd_args = cmd_formatted.split(" ")
        p = start_process(cmd_args)
        return p

    def stop_monitor(self, monitor_process):
        ack = stop_process(monitor_process)
        return ack

    async def call_directrix(self, stub, action):

        targets = repr(set(["hammurabi"]))
        broker_address = "127.0.0.1:50052"

        data = {
            "action": action,
            "flush": {
                "live": True,
                "environment": "x",
                "address": broker_address,
            },
            "sources": [
                {
                    "id": 1,
                    "name": "container",
                    "parameters": {
                        "targets": targets,
                        "duration": "3600",
                        "interval": "5",
                    },
                    "schedule": {},
                },
                {
                    "id": 2,
                    "name": "host",
                    "parameters": {
                        "duration": "3600",
                        "interval": "5",
                    },
                    "schedule": {},
                },
            ],
        }

        request = json_format.ParseDict(data, Directrix())

        reply = await stub.Measure(request)
        reply_dict = json_format.MessageToDict(reply)

        return reply_dict

    async def run_directrix(self):
        uuid, address = "monitor-test", "127.0.0.1:50051"
        monitor_p = self.start_monitor(uuid, address)

        uuid, address = "broker-test", "127.0.0.1:50052"
        broker_p = self.start_broker(uuid, address)

        try:
            await asyncio.sleep(1.0)
            channel = Channel("127.0.0.1", 50051)
            stub = MonitorStub(channel)

            action = "start"
            info_reply = await self.call_directrix(stub, action)

            await asyncio.sleep(10)

            action = "stop"
            info_reply = await self.call_directrix(stub, action)

        except Exception as e:
            logger.info(f"run directrix exception - {repr(e)}")
            info_reply = None

        finally:
            channel.close()

        ack = self.stop_monitor(monitor_p)
        assert ack == True

        ack = self.stop_broker(broker_p)
        assert ack == True

        return info_reply

    def test_directrix(self):

        stats_reply = asyncio.run(self.run_directrix())
        print(stats_reply)

        # assert info_reply.get("role") == "agent"
        # assert info_reply.get("address") == "127.0.0.1:50051"

        # probers = info_reply.get("artifacts").get("probers")
        # ping_prober_ls = [p for p in probers if p.get("id") == 2]
        # ping_prober = ping_prober_ls.pop()

        # assert ping_prober.get("name") == "ping"

        # assert instruction_reply.get("trial") == 1
        # assert origin.get("id") == "agent-test"
        # assert origin.get("role") == "agent"

        # evals = instruction_reply.get("evaluations")
        # assert type(evals) is list

        # expected_metrics = {
        #     "rtt_min": "min round-trip-time",
        #     "rtt_avg": "avg round-trip-time",
        #     "rtt_max": "max round-trip-time",
        #     "rtt_mdev": "std dev round-trip-time",
        #     "frame_loss": "frame loss ratio",
        # }

        # print(json.dumps(instruction_reply, indent=4))

        # eval_0 = evals[0]
        # eval_metrics = eval_0.get("metrics")

        # expected = list(expected_metrics.keys())
        # metrics_ok = [
        #     True if m.get("name") in expected else False for m in eval_metrics
        # ]

        # assert all(metrics_ok) == True


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s",
    )

    unittest.main()
