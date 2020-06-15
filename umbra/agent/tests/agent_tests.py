import logging
import sys
import json 

sys.path.append("/home/raphael/git/playground/control_loop/cl-ems")

level = logging.DEBUG
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
handler.setLevel(level)
logging.getLogger().addHandler(handler)
logging.getLogger().setLevel(level)
logger = logging.getLogger(__name__)


from umbra.agent.tools import Tools


class Tests:
    def __init__(self):
        self.tools = Tools()

    def test_pings(self):
        instructions = {
            1: {
                'tool-id': 3,
                'parameters': {
                    'packets': 3,
                    'target': '127.0.0.1',
                }
            },
            2: {
                'tool-id': 3,
                'parameters': {
                    'packets': 6,
                    'target': '8.8.8.8',
                }
            },
        }
        self.call(instructions)


    def test_iperf(self):
        instructions = {
            1: {
                'tool-id': 2,
                'parameters': {
                    'port': 9030,
                    'duration': 2,
                    'client': True,
                    'server': '127.0.0.1',
                }
            },
            2: {
                'tool-id': 2,
                'parameters': {
                    'port': 9030,
                    'duration': 2,
                    'client': False,
                }
            },
        }
        self.call(instructions)


    def test_tcpreplay(self):
        instructions = {
            1: {
                'tool-id': 1,
                'parameters': {
                    'interface': 'lo',
                    'duration': 5,
                    'pcap': 'bigFlows.pcap',
                }
            },
        }
        self.call(instructions)

    def test_caddy(self):
        instructions = {
            1: {
                'tool-id': 4,
                'parameters': {
                    'duration': 5,
                    'folder': '/mnt/pcaps/',
                }
            },
        }
        self.call(instructions)

    def test_dashc(self):
        instructions = {
            1: {
                'tool-id': 5,
                'parameters': {
                    'mpd': 'http://www.cs.ucc.ie/~jq5/www_dataset_temp/x264_6sec/bbb_10min/DASH_Files/VOD/bbb_enc_10min_x264_dash.mpd',
                    'adapt': 'bba-0',
                }
            },
        }
        self.call(instructions)

    def call(self, data):
        evals = self.tools.act(data)
        print(evals)

    def run(self):
        # self.test_pings()
        # self.test_iperf()
        # self.test_tcpreplay()
        # self.test_caddy()
        self.test_dashc()

if __name__ == "__main__":
    tests = Tests()
    tests.run()
