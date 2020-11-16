import logging

from umbra.design.basis import Experiment
from umbra.design.iroha import IrohaTopology


logger = logging.getLogger(__name__)


def build():
    iroha_topo = IrohaTopology("local-3nodes")

    experiment = Experiment("local-3nodes")
    experiment.set_topology(iroha_topo)

    iroha_topo.add_iroha_node("node1", "nodes")
    iroha_topo.add_iroha_node("node2", "nodes")
    iroha_topo.add_iroha_node("node3", "nodes")

    iroha_topo.add_network("s1", envid="umbra-default")

    iroha_topo.add_link_node_network("node3", "s1", "links")
    iroha_topo.add_link_node_network("node2", "s1", "links")
    iroha_topo.add_link_node_network("node1", "s1", "links")

    node_resources = iroha_topo.create_node_profile(cpus=2, memory=2048, disk=None)
    link_resources = iroha_topo.create_link_profile(bw=10, delay=None, loss=None)

    iroha_topo.add_node_profile(node_resources, profile="nodes")
    iroha_topo.add_link_profile(link_resources, profile="links")

    ev_01 = {
        "action": "create_domain",
        "node": "node2",
        "user": "admin",
        "domain": "umbra2",
        "default_role": "user",
    }

    ev_02 = {
        "action": "create_account",
        "node": "node2",
        "user": "admin",
        "domain": "umbra",
        "account_pubkey": "c4dec3e3478dca78af4bde6fd3d533f99426cdb73c655b45e597216207969d47",
        "account_name": "irohatester",
    }

    ev_03 = {
        "node": "node2",
        "user": "admin",
        "action": "set_account_detail",
        "account_id": "admin@umbra",
        "account_detail_name": "age",
        "account_detail_value": "18",
    }

    ev_04 = {
        "node": "node2",
        "user": "admin",
        "action": "create_asset",
        "domain": "umbra",
        "asset_name": "vidas",
        "asset_precision": 2,
    }

    ev_05 = {
        "node": "node2",
        "user": "admin",
        "action": "add_asset_quantity",
        "asset_id": "vidas#umbra",
        "asset_amount": "500.00",
    }

    ev_06 = {
        "node": "node2",
        "user": "admin",
        "action": "transfer_asset",
        "asset_id": "vidas#umbra",
        "asset_amount": "50.00",
        "src_account_id": "admin@umbra",
        "dest_account_id": "test@umbra",
        "description": "plus vidas",
    }

    ev_07 = {
        "node": "node2",
        "user": "admin",
        "action": "get_asset_info",
        "asset_id": "vidas#umbra",
    }

    ev_08 = {
        "node": "node2",
        "user": "admin",
        "action": "get_account_assets",
        "account_id": "admin@umbra",
    }

    ev_09 = {
        "node": "node2",
        "user": "admin",
        "action": "get_account_detail",
        "account_id": "admin@umbra",
    }

    ev_10 = {
        "node": "node2",
        "user": "admin",
        "action": "grant_permission",
        "account_id": "admin@umbra",
        "account": "test@umbra",
        "permission": "can_set_my_account_detail",
    }

    sched_ev_01 = {"from": 11}
    sched_ev_02 = {"from": 13}
    sched_ev_03 = {"from": 15}
    sched_ev_04 = {"from": 17}
    sched_ev_05 = {"from": 19}
    sched_ev_06 = {"from": 21}
    sched_ev_07 = {"from": 23}
    sched_ev_08 = {"from": 25}
    sched_ev_09 = {"from": 27}
    sched_ev_10 = {"from": 30}

    experiment.add_event(sched=sched_ev_01, category="iroha", event=ev_01)
    experiment.add_event(sched=sched_ev_02, category="iroha", event=ev_02)
    experiment.add_event(sched=sched_ev_03, category="iroha", event=ev_03)
    experiment.add_event(sched=sched_ev_04, category="iroha", event=ev_04)
    experiment.add_event(sched=sched_ev_05, category="iroha", event=ev_05)
    experiment.add_event(sched=sched_ev_06, category="iroha", event=ev_06)
    experiment.add_event(sched=sched_ev_07, category="iroha", event=ev_07)
    experiment.add_event(sched=sched_ev_08, category="iroha", event=ev_08)
    experiment.add_event(sched=sched_ev_09, category="iroha", event=ev_09)
    experiment.add_event(sched=sched_ev_10, category="iroha", event=ev_10)

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
    setup_logging()
    build()
