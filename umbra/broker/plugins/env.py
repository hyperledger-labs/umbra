import logging
import json

from datetime import datetime
from grpclib.client import Channel
from umbra.common.protobuf.umbra_grpc import ScenarioStub
from umbra.common.protobuf.umbra_pb2 import Report, Workflow
from umbra.common.scheduler import Handler

logger = logging.getLogger(__name__)

class EnvEventHandler():
    def __init__(self):
        self.handler = Handler()
        # url:port address for umbra-scenario
        self.address = None
        self.wflow_id = None

    def config(self, address, wflow_id):
        self.address = address
        self.wflow_id = wflow_id

    def build_calls(self, events):
        calls = {}

        for event_id, event_args in events.items():
            params = event_args.get('params', {})
            env_event = EnvEvent(self.address, self.wflow_id, params['command'], params['args'])
            action_call = env_event.call_scenario
            action_sched = params.get('schedule', {})
            calls[event_id] = (action_call, action_sched)

        return calls

    async def handle(self, events):
        calls = self.build_calls(events)
        results = await self.handler.run(calls)

class EnvEvent():
    def __init__(self, address, wflow_id, command, wflow_scenario):
        self.address = address
        self.wflow_id = wflow_id
        self.command = command
        self.wflow_scenario = wflow_scenario

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

    async def call_scenario(self):
        logger.debug(f"START call_scenario: {self.wflow_scenario}")

        self.wflow_scenario = self.serialize_bytes(self.wflow_scenario)
        deploy = Workflow(id=self.wflow_id, workflow=self.command, scenario=self.wflow_scenario)
        deploy.timestamp.FromDatetime(datetime.now())

        host, port = self.address.split(":")
        channel = Channel(host, port)
        stub = ScenarioStub(channel)
        status = await stub.Establish(deploy)

        if status.error:
            ack = False
            logger.warn(f'call_scenario FAIL: {status.error}')
        else:
            ack = True
            info = self.parse_bytes(status.info)
            logger.debug(f'info = {info}')

        channel.close()
        return ack, info
