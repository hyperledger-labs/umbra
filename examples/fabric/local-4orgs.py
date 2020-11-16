import os
import logging

from umbra.design.basis import Experiment
from umbra.design.fabric import FabricTopology

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

    fab_topo = FabricTopology("local-4orgs", chaincode_dir=chaincode_dir)

    experiment = Experiment("local-4orgs")
    experiment.set_topology(fab_topo)

    fab_topo.add_network("s1", envid="umbra-default")
    fab_topo.add_network("s2", envid="umbra-default")

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

    # If needed you can multiplex nodes of a org to be connected to separate networks
    # Use the function add_node_network_link, with the params (org, node_name, network, profile_name)
    fab_topo.add_node_network_link("org1", "peer0", "s1", "links")
    fab_topo.add_node_network_link("org1", "peer1", "s2", "links")
    fab_topo.add_node_network_link("org1", "ca", "s2", "links")
    # fab_topo.add_org_network_link("org1", "s1", "links")
    fab_topo.add_node_network_link("org2", "peer0", "s1", "links")
    fab_topo.add_node_network_link("org2", "peer1", "s2", "links")
    fab_topo.add_node_network_link("org2", "ca", "s2", "links")
    # fab_topo.add_org_network_link("org2", "s2", "links")
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
