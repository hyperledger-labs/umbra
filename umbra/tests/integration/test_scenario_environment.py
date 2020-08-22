import unittest

from umbra.scenario.environment import Environment


class TestEnvironment(unittest.TestCase):
    def test_docker_network(self):
        env = Environment({})

        ack = env.create_docker_network()

        assert ack is True

        nack = env.remove_docker_network()

        assert nack is True


if __name__ == "__main__":
    unittest.main()
