import os
import sys
import logging

from umbra.design.configs import Profile, Topology, Scenario
from umbra.design.configs import FabricTopology

from base_configtx.fabric import (
    org1_policy,
    org2_policy,
    org3_policy,
    org4_policy,
    orderer_policy,
    configtx,
)


def build_simple_fabric_cfg():

    # temp_dir = "/tmp/umbra/fabric_configs"
    # configs_dir = os.path.abspath(os.path.join(temp_dir))

    # temp_dir = "/tmp/umbra/chaincode"
    # chaincode_dir = os.path.abspath(os.path.join(temp_dir))

    # Defines Fabric Topology - main class to have orgs/peers/cas/orderers added
    fab_topo = FabricTopology("fabric_simple")

    # Defines scenario containing topology, so events can be added

    scenario = Scenario("Fabric-Simple-01")
    scenario.set_topology(fab_topo)

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

    fab_topo.add_network("s1")
    fab_topo.add_network("s2")

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

    # Configtx quick fixes - checks which paths from configtx needs to have full org desc
    fab_topo.configtx(configtx)
    p1 = "TwoOrgsOrdererGenesis.Consortiums.SampleConsortium.Organizations"
    p2 = "TwoOrgsOrdererGenesis.Orderer.Organizations"
    p3 = "TwoOrgsChannel.Application.Organizations"
    fab_topo.set_configtx_profile(p1, ["org1", "org2", "org3", "org4"])
    fab_topo.set_configtx_profile(p2, ["orderer"])
    fab_topo.set_configtx_profile(p3, ["org1", "org2", "org3", "org4"])

    # Creates all config files - i.e., crypto-config configtx config-sdk
    fab_topo.build_configs()

    fab_topo.add_org_network_link("org1", "s1", "links")
    fab_topo.add_org_network_link("org2", "s2", "links")
    fab_topo.add_org_network_link("org3", "s1", "links")
    fab_topo.add_org_network_link("org4", "s2", "links")
    fab_topo.add_org_network_link("orderer", "s1", "links")

    # Defines resources for nodes and links
    node_resources = fab_topo.create_node_profile(cpus=1, memory=1024, disk=None)
    link_resources = fab_topo.create_link_profile(bw=1, delay="2ms", loss=None)

    fab_topo.add_node_profile(node_resources, profile="nodes")
    fab_topo.add_link_profile(link_resources, profile="links")

    # topo_built = fab_topo.build()
    # print(topo_built)
    # fab_topo.show()

    ev_create_channel = {
        "action": "create_channel",
        "org": "org1",
        "user": "Admin",
        "orderer": "orderer",
        "channel": "testchannel",
        "profile": "TwoOrgsChannel",
    }

    ev_join_channel_org1 = {
        "action": "join_channel",
        "org": "org1",
        "user": "Admin",
        "orderer": "orderer",
        "channel": "testchannel",
        "peers": ["peer0", "peer1"],
    }

    ev_join_channel_org2 = {
        "action": "join_channel",
        "org": "org2",
        "user": "Admin",
        "orderer": "orderer",
        "channel": "testchannel",
        "peers": ["peer0", "peer1"],
    }

    ev_join_channel_org3 = {
        "action": "join_channel",
        "org": "org3",
        "user": "Admin",
        "orderer": "orderer",
        "channel": "testchannel",
        "peers": ["peer0"],
    }

    ev_join_channel_org4 = {
        "action": "join_channel",
        "org": "org4",
        "user": "Admin",
        "orderer": "orderer",
        "channel": "testchannel",
        "peers": ["peer0"],
    }

    ev_info_channel = {
        "action": "info_channel",
        "org": "org1",
        "user": "Admin",
        "channel": "testchannel",
        "peers": ["peer0"],
    }

    ev_info_channel_config = {
        "action": "info_channel_config",
        "org": "org1",
        "user": "Admin",
        "channel": "testchannel",
        "peers": ["peer0"],
    }

    ev_info_channels = {
        "action": "info_channels",
        "org": "org1",
        "user": "Admin",
        "peers": ["peer0"],
    }

    ev_info_network = {
        "action": "info_network",
        "orderer": "orderer",
    }

    ev_chaincode_install_org1 = {
        "action": "chaincode_install",
        "org": "org1",
        "user": "Admin",
        "chaincode_name": "example_cc",
        "chaincode_path": "github.com/example_cc",
        "chaincode_version": "v1.0",
        "peers": ["peer0", "peer1"],
    }

    ev_chaincode_install_org2 = {
        "action": "chaincode_install",
        "org": "org2",
        "user": "Admin",
        "chaincode_name": "example_cc",
        "chaincode_path": "github.com/example_cc",
        "chaincode_version": "v1.0",
        "peers": ["peer0", "peer1"],
    }

    ev_chaincode_instantiate_org1 = {
        "action": "chaincode_instantiate",
        "org": "org1",
        "user": "Admin",
        "peers": ["peer1"],
        "channel": "testchannel",
        "chaincode_name": "example_cc",
        "chaincode_args": ["a", "200", "b", "50"],
        "chaincode_version": "v1.0",
    }

    ev_chaincode_instantiate_org2 = {
        "action": "chaincode_instantiate",
        "org": "org2",
        "user": "Admin",
        "peers": ["peer1"],
        "channel": "testchannel",
        "chaincode_name": "example_cc",
        "chaincode_args": ["a", "200", "b", "50"],
        "chaincode_version": "v1.0",
    }

    ev_chaincode_invoke_org1 = {
        "action": "chaincode_invoke",
        "org": "org1",
        "user": "Admin",
        "peers": ["peer1"],
        "channel": "testchannel",
        "chaincode_name": "example_cc",
        "chaincode_args": ["a", "b", "100"],
    }

    ev_chaincode_query_org1 = {
        "action": "chaincode_query",
        "org": "org2",
        "user": "Admin",
        "peers": ["peer1"],
        "channel": "testchannel",
        "chaincode_name": "example_cc",
        "chaincode_args": ["b"],
    }

    ev_chaincode_query_org2 = {
        "action": "chaincode_query",
        "org": "org2",
        "user": "Admin",
        "peers": ["peer1"],
        "channel": "testchannel",
        "chaincode_name": "example_cc",
        "chaincode_args": ["b"],
    }

    # scenario.add_event("0", "fabric", ev_info_channels)
    # scenario.add_event("1", "fabric", ev_create_channel)
    # scenario.add_event("3", "fabric", ev_join_channel_org1)
    # scenario.add_event("3", "fabric", ev_join_channel_org2)
    # scenario.add_event("3", "fabric", ev_join_channel_org3)
    # scenario.add_event("3", "fabric", ev_join_channel_org4)
    # scenario.add_event("4", "fabric", ev_info_channel)
    # scenario.add_event("5", "fabric", ev_info_channel_config)
    # scenario.add_event("6", "fabric", ev_info_channels)
    # scenario.add_event("7", "fabric", ev_info_network)
    # scenario.add_event("8", "fabric", ev_chaincode_install_org1)
    # scenario.add_event("8", "fabric", ev_chaincode_install_org2)
    # scenario.add_event("10", "fabric", ev_chaincode_instantiate_org1)
    # scenario.add_event("10", "fabric", ev_chaincode_instantiate_org2)
    # scenario.add_event("20", "fabric", ev_chaincode_invoke_org1)
    # scenario.add_event("30", "fabric", ev_chaincode_query_org1)
    # scenario.add_event("32", "fabric", ev_chaincode_query_org2)

    # Save config file
    scenario.save()


def builds():
    build_simple_fabric_cfg()


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
    builds()
