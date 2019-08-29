import os
import sys
import logging

from umbra_cfgs.config import Profile, Topology, Scenario, Cfg
from umbra_cfgs.config import FabricTopology

from base_configtx.fabric import org1_policy, org2_policy, orderer_policy, configtx


def build_simple_fabric_cfg():
    temp_dir = "./fabric_configs"
    configs_dir = os.path.normpath(
        os.path.join(
            os.path.dirname(__file__), temp_dir))

    temp_dir = "./chaincode"
    chaincode_dir = os.path.normpath(
        os.path.join(
            os.path.dirname(__file__), temp_dir))

    fab_topo = FabricTopology('fabric_simple', configs_dir, chaincode_dir)

    domain = "example.com"
    image_tag = "1.4.0.1"

    fab_topo.add_org("org1", domain, None, policies=org1_policy)
    fab_topo.add_peer("peer0", "org1", anchor=True, image_tag=image_tag)
    fab_topo.add_peer("peer1", "org1", image_tag=image_tag)

    fab_topo.add_org("org2", domain, None, policies=org2_policy)
    fab_topo.add_peer("peer0", "org2", anchor=True, image_tag=image_tag)
    fab_topo.add_peer("peer1", "org2", image_tag=image_tag)

    ord_specs = [
        {"Hostname": "orderer"},
        {"Hostname": "orderer2"},
        {"Hostname": "orderer3"},
        {"Hostname": "orderer4"},
        {"Hostname": "orderer5"},
    ] 

    fab_topo.add_orderer("orderer", domain, mode="solo", specs=ord_specs, policies=orderer_policy, image_tag=image_tag)

    fab_topo.add_ca("ca", "org1", domain, "admin", "admin_pw", image_tag=image_tag)
    fab_topo.add_ca("ca", "org2", domain, "admin", "admin_pw", image_tag=image_tag)

    fab_topo.configtx(configtx)

    p1 = "TwoOrgsOrdererGenesis.Consortiums.SampleConsortium.Organizations"
    p2 = "TwoOrgsOrdererGenesis.Orderer.Organizations"
    p3 = "TwoOrgsChannel.Application.Organizations"
    fab_topo.set_configtx_profile(p1, ["org1", "org2"])
    fab_topo.set_configtx_profile(p2, ["orderer"])
    fab_topo.set_configtx_profile(p3, ["org1", "org2"])

    fab_topo.build_configs()

    fab_topo.add_network("s0")

    fab_topo.add_org_network_link("org1", "s0", "E-Line")
    fab_topo.add_org_network_link("org2", "s0", "E-Line")
    fab_topo.add_org_network_link("orderer", "s0", "E-Line")

    node_resources = fab_topo.create_node_profile(cpus=1, memory=1024, disk=None)
    link_resources = fab_topo.create_link_profile(bw=1, delay='2ms', loss=None)
    
    fab_topo.add_node_profile(node_resources, node_type="container")
    fab_topo.add_link_profile(link_resources, link_type="E-Line")
    
    topo_built = fab_topo.build()
    # print(topo_built)
    # fab_topo.show()

    scenario = Scenario("scenario_fabric", "Tester")
    scenario.set_topology(fab_topo)

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
        "peers": ["peer0"],
        "channel": "testchannel",
        "chaincode_name": "example_cc",
        "chaincode_args": ['a', '200', 'b', '300'],
        "chaincode_version": "v1.0",        
    }

    ev_chaincode_invoke_org1 = {
        "action": "chaincode_invoke",
        "org": "org1",
        "user": "Admin",
        "peers": ["peer0"],
        "channel": "testchannel",
        "chaincode_name": "example_cc",
        "chaincode_args": ['a', 'b', '100'],
    }


    ev_chaincode_query_org1 = {
        "action": "chaincode_query",
        "org": "org1",
        "user": "Admin",
        "peers": ["peer0"],
        "channel": "testchannel",
        "chaincode_name": "example_cc",
        "chaincode_args": ['b'],
    }

    scenario.add_event("0", "fabric", ev_info_channels)
    scenario.add_event("1", "fabric", ev_create_channel)
    scenario.add_event("3", "fabric", ev_join_channel_org1)
    scenario.add_event("3", "fabric", ev_join_channel_org2)
    scenario.add_event("4", "fabric", ev_info_channel)
    scenario.add_event("5", "fabric", ev_info_channel_config)
    scenario.add_event("6", "fabric", ev_info_channels)
    scenario.add_event("7", "fabric", ev_info_network)
    scenario.add_event("8", "fabric", ev_chaincode_install_org1)
    scenario.add_event("8", "fabric", ev_chaincode_install_org2)
    scenario.add_event("10", "fabric", ev_chaincode_instantiate_org1)
    scenario.add_event("16", "fabric", ev_chaincode_invoke_org1)
    scenario.add_event("20", "fabric", ev_chaincode_query_org1)

    cfg = Cfg("config_fabric_simple", configs_dir)
    cfg.set_scenario(scenario)
    cfg.deploy(plugin="containernet", entrypoint="http://172.17.0.1:8988/001/")
    cfg.save()


def setup_logging(log_level=logging.INFO):
    """Set up the logging."""
    logging.basicConfig(level=log_level)
    fmt = ("%(asctime)s %(levelname)s (%(threadName)s) "
           "[%(name)s] %(message)s")
    colorfmt = "%(log_color)s{}%(reset)s".format(fmt)
    datefmt = '%Y-%m-%d %H:%M:%S'

    try:
        from colorlog import ColoredFormatter
        logging.getLogger().handlers[0].setFormatter(ColoredFormatter(
            colorfmt,
            datefmt=datefmt,
            reset=True,
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red',
            }
        ))
    except ImportError:
        pass

    logger = logging.getLogger('')
    logger.setLevel(log_level) 

def builds():
    build_simple_fabric_cfg()


if __name__ == "__main__":
    setup_logging()
    builds()