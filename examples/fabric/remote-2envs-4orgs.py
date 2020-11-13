import os
import logging

from umbra.design.configs import Experiment, FabricTopology

from base_configtx.configtx_4orgs import (
    org1_policy,
    org2_policy,
    org3_policy,
    org4_policy,
    orderer_policy,
    configtx,
)


def builds():

    temp_dir = "/tmp/umbra/fabric/chaincode"
    chaincode_dir = os.path.abspath(os.path.join(temp_dir))

    fab_topo = FabricTopology("remote-2envs-4orgs", chaincode_dir=chaincode_dir)

    experiment = Experiment("remote-2envs-4orgs")
    experiment.set_topology(fab_topo)

    umbra_default = {
        "id": "umbra-default",
        "remote": False,
        "host": {},
        "components": {
            # "scenario": {
            #     "uuid": "default-scenario",
            #     "address": "192.168.122.1:8957",
            # },
            "broker": {
                "uuid": "default-broker",
                "address": "192.168.122.1:8956",
            },
        },
    }

    fab_topo.set_default_environment(umbra_default)

    env0_id = "env44"
    env0_info = {
        "id": env0_id,
        "remote": True,
        "host": {
            "user": "umbra",
            "address": "192.168.122.44",
            "port": "22",
            "password": "L1v3s.",
        },
        "components": {
            "scenario": {
                "uuid": "y-scenario",
                "address": "192.168.122.44:8957",
            },
            "monitor": {
                "uuid": "y-monitor",
                "address": "192.168.122.44:8958",
            },
        },
    }

    env1_id = "env156"
    env1_info = {
        "id": env1_id,
        "remote": True,
        "host": {
            "user": "umbra",
            "address": "192.168.122.156",
            "port": "22",
            "password": "L1v3s.",
        },
        "components": {
            "scenario": {
                "uuid": "z-scenario",
                "address": "192.168.122.156:8957",
            },
            "monitor": {
                "uuid": "z-monitor",
                "address": "192.168.122.156:8958",
            },
        },
    }

    fab_topo.add_environment(env=env0_info)
    fab_topo.add_environment(env=env1_info)

    fab_topo.add_network("s1", envid=env0_id)
    fab_topo.add_network("s2", envid=env1_id)

    fab_topo.add_networks_link(src="s1", dst="s2")

    domain = "example.com"
    image_tag = "2.2.1"
    ca_tag = "1.4.7.1"

    fab_topo.add_org("org1", domain, policies=org1_policy)
    fab_topo.add_peer(
        "peer0", "org1", anchor=True, profile="nodes", image_tag=image_tag
    )
    fab_topo.add_peer("peer1", "org1", profile="nodes", image_tag=image_tag)

    fab_topo.add_org("org2", domain, policies=org2_policy)
    fab_topo.add_peer(
        "peer0", "org2", anchor=True, profile="nodes", image_tag=image_tag
    )
    fab_topo.add_peer("peer1", "org2", profile="nodes", image_tag=image_tag)

    fab_topo.add_org("org3", domain, policies=org3_policy)
    fab_topo.add_peer(
        "peer0", "org3", anchor=True, profile="nodes", image_tag=image_tag
    )

    fab_topo.add_org("org4", domain, policies=org4_policy)
    fab_topo.add_peer(
        "peer0", "org4", anchor=True, profile="nodes", image_tag=image_tag
    )

    ord_specs = [
        {
            "Hostname": "orderer",
            "SANS": ["localhost"],
        },
    ]

    fab_topo.add_orderer(
        "orderer",
        domain,
        profile="nodes",
        mode="raft",
        specs=ord_specs,
        policies=orderer_policy,
        image_tag=image_tag,
    )

    fab_topo.add_ca(
        "ca", "org1", domain, "admin", "admin_pw", profile="nodes", image_tag=ca_tag
    )
    fab_topo.add_ca(
        "ca", "org2", domain, "admin", "admin_pw", profile="nodes", image_tag=ca_tag
    )
    fab_topo.add_ca(
        "ca", "org3", domain, "admin", "admin_pw", profile="nodes", image_tag=ca_tag
    )
    fab_topo.add_ca(
        "ca", "org4", domain, "admin", "admin_pw", profile="nodes", image_tag=ca_tag
    )

    fab_topo.configtx(configtx)
    p1 = "TwoOrgsOrdererGenesis.Consortiums.SampleConsortium.Organizations"
    p2 = "TwoOrgsOrdererGenesis.Orderer.Organizations"
    p3 = "TwoOrgsChannel.Application.Organizations"
    fab_topo.set_configtx_profile(p1, ["org1", "org2", "org3", "org4"])
    fab_topo.set_configtx_profile(p2, ["orderer"])
    fab_topo.set_configtx_profile(p3, ["org1", "org2", "org3", "org4"])

    fab_topo.add_org_network_link("org1", "s1", "links")
    fab_topo.add_org_network_link("org2", "s2", "links")
    fab_topo.add_org_network_link("org3", "s1", "links")
    fab_topo.add_org_network_link("org4", "s2", "links")
    fab_topo.add_org_network_link("orderer", "s1", "links")

    node_resources = fab_topo.create_node_profile(cpus=1, memory=1024, disk=None)
    link_resources = fab_topo.create_link_profile(bw=1, delay="2ms", loss=None)

    fab_topo.add_node_profile(node_resources, profile="nodes")
    fab_topo.add_link_profile(link_resources, profile="links")

    # Save config file
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
    builds()
