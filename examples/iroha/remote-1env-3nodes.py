import logging

from umbra.design.basis import Experiment
from umbra.design.iroha import IrohaTopology


logger = logging.getLogger(__name__)


def build():
    iroha_topo = IrohaTopology("remote-1env-3nodes")
    experiment = Experiment("remote-1env-3nodes")
    experiment.set_topology(iroha_topo)

    umbra_default = {
        "id": "umbra-default",
        "remote": False,
        "host": {"address": "localhost"},
        "components": {
            "broker": {
                "uuid": "default-broker",
                "address": "192.168.121.1:8956",
            },
        },
    }

    iroha_topo.set_default_environment(umbra_default)

    env_id = "env_remote"
    env_info = {
        "id": env_id,
        "remote": True,
        "host": {
            "user": "umbra",
            "address": "192.168.121.101",
            "port": "22",
            "password": "L1v3s.",
        },
        "components": {
            "scenario": {
                "uuid": "remote-scenario",
                "address": "192.168.121.101:8957",
            },
            "monitor": {
                "uuid": "remote-monitor",
                "address": "192.168.121.101:8958",
            },
        },
    }
    iroha_topo.add_environment(env=env_info)

    iroha_topo.add_iroha_node("node1", "nodes")
    iroha_topo.add_iroha_node("node2", "nodes")
    iroha_topo.add_iroha_node("node3", "nodes")

    iroha_topo.add_network("s1", envid=env_id)

    iroha_topo.add_link_node_network("node3", "s1", "links")
    iroha_topo.add_link_node_network("node2", "s1", "links")
    iroha_topo.add_link_node_network("node1", "s1", "links")

    node_resources = iroha_topo.create_node_profile(cpus=2, memory=2048, disk=None)
    link_resources = iroha_topo.create_link_profile(bw=10, delay="1ms", loss=None)

    iroha_topo.add_node_profile(node_resources, profile="nodes")
    iroha_topo.add_link_profile(link_resources, profile="links")

    experiment.save()


def setup_logging(log_level=logging.DEBUG):
    """Set up the logging."""
    logging.basicConfig(level=log_level)
    fmt = "%(asctime)s %(levelname)s (%(threadName)s) " "[%(name)s] %(message)s"
    colorfmt = "%(log_color)s{}%(reset)s".format(fmt)
    datefmt = "%Y-%m-%d %H:%M:%S"

    try:
        from colorlog import ColoredFormatter

        logging.getLogger().handlers[0].setFormatter(
            ColoredFormatter(
                colorfmt,
                datefmt=datefmt,
                reset=True,
                log_colors={
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "red",
                },
            )
        )
    except ImportError:
        pass

    logger = logging.getLogger("")
    logger.setLevel(log_level)


if __name__ == "__main__":
    # setup_logging()
    build()
