import unittest
import logging
import shlex


from umbra.cli.envs import LocalPlugin, RemotePlugin


logger = logging.getLogger(__name__)


class TestCLI(unittest.TestCase):
    def start_command(self, lp):
        start_cmd = "sudo umbra-broker --uuid default-scenario --address 127.0.0.1:8990 --debug &"

        ack, msg = lp.execute_command(start_cmd, daemon=True)
        # print(msg)
        return ack

    def stop_command(self, lp):
        stop_cmd = "sudo pkill -9 'umbra-broker'"
        ack, msg = lp.execute_command(stop_cmd)
        # print(msg)
        return ack

    def test_clirunner_local_exec_command(self):
        lp = LocalPlugin()

        ack = self.start_command(lp)
        assert ack == True

        ack = self.stop_command(lp)
        assert ack == True

    # def test_clirunner_remote_exec_command(self):
    #     rp = RemotePlugin()
    #     cfg = {
    #         "user": "umbra",
    #         "address": "192.168.122.44",
    #         "port": "22",
    #         "password": "L1v3s.",
    #     }
    #     rp.cfg(cfg)
    #     ack = self.start_command(rp)
    #     assert ack == True

    #     ack = self.stop_command(rp)
    #     assert ack == True


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
