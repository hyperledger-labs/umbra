import os
import logging

# First of all, import from umbra-design the configs that
# refer to the construction of your Experiment using the
# FabricTopology API.
from umbra.design.basis import Experiment
from umbra.design.fabric import FabricTopology

# Then, import the configtx definitions, which are going
# to be used by each one of the orgs policies, and also
# for the whole construction of the configtx.yml file.
from base_configtx.configtx_2orgs import (
    org1_policy,
    org2_policy,
    orderer_policy,
    configtx,
)


def builds():

    # Umbra keeps everything in /tmp/umbra, and in the case of fabric
    # the configs generated will be in /tmp/umbra/fabric/"name of the experiment".

    temp_dir = "/tmp/umbra/fabric/chaincode"
    chaincode_dir = os.path.abspath(os.path.join(temp_dir))

    # Defines Fabric Topology - main class to have orgs/peers/cas/orderers
    # From the FabricTopology, it is possible to define the whole set of orgs,
    # peers, CAs and orderers that compose the network experiment.
    # The chaincode directory can be specified if the events of the experiment
    # make use of any of the chaincodes in that dir, so umbra knows the right
    # place to look for them.
    fab_topo = FabricTopology("remote-1envs-2orgs", chaincode_dir=chaincode_dir)

    # Defines experiment containing topology, later events can be added.
    # An experiment consists of a topology and events. It sets the ground for
    # what is going to actually be instantiated and executed.
    experiment = Experiment("remote-1envs-2orgs")
    experiment.set_topology(fab_topo)

    # Environments in umbra are the places (i.e., baremetal servers and/or virtual machines)
    # where the components of umbra are executed, and consequently the topology itself.
    # An environment can be remote or local (parameter remote set to true or false).
    # The definitions inside host must contain the parameters (user, address, port, password)
    # needed to execute commands in the remote environment.
    # The user must be allowed to execute operations as sudo in the environment.
    # In a local environment, (remote set to false), the user will be the logged in user
    # that used to instantiate and run umbra.

    # Environment umbra-default will only contain umbra-broker component
    # It means umbra-cli is goint to reach to umbra-broker in order to interact
    # with the other environments.
    # The broker address must be the one that interfaces the other environments
    # In the example below it is the bridge gateway address that is used by the
    # virtual machine that executes the other environment.
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

    # The topology must be configured with the new umbra-default settings
    fab_topo.set_default_environment(umbra_default)

    # Defines the environment that the scenario and the other components are
    # going to be instantiated.

    # Umbra realizes a network is associated with an environment, and it realizes
    # all the nodes interconnected to this network are also in the same environment
    # as the network. All the proper settings regarding the reachability of
    # the nodes, network, environment is handled by umbra.
    # The most important feature is the definition of the correct addresses
    # for the umbra components, which must be reachable by umbra-broker.
    env0_id = "env44"
    env0_info = {
        "id": env0_id,
        "remote": True,
        "host": {
            "user": "umbra",
            "address": "192.168.122.101",
            "port": "22",
            "password": "L1v3s.",
        },
        "components": {
            "scenario": {
                "uuid": "y-scenario",
                "address": "192.168.121.101:8957",
            },
            "monitor": {
                "uuid": "y-monitor",
                "address": "192.168.121.101:8958",
            },
        },
    }
    fab_topo.add_environment(env=env0_info)

    # The network must be associated with the environment where it is going
    # to be placed/executed. All the nodes connected to the network will be deployed
    # in the environment where the network is placed.
    fab_topo.add_network("s1", envid=env0_id)

    # The definitions of the fabric topology settings, e.g., domain and tag of the
    # container images that are going to be used to instantiate the fabric nodes.
    domain = "example.com"
    image_tag = "2.2.1"
    ca_tag = "1.4.7.1"

    # The topology can be composed by orgs and their peers.
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

    ord_specs = [
        {
            "Hostname": "orderer",
            "SANS": ["localhost"],
        },
    ]

    # The topology can be composed by orderers with their proper parameters.
    fab_topo.add_orderer(
        "orderer",
        domain,
        profile="nodes",
        mode="raft",
        specs=ord_specs,
        policies=orderer_policy,
        image_tag=image_tag,
    )

    # The topology can be composed by CAs with their proper parameters.
    fab_topo.add_ca(
        "ca", "org1", domain, "admin", "admin_pw", profile="nodes", image_tag=ca_tag
    )
    fab_topo.add_ca(
        "ca", "org2", domain, "admin", "admin_pw", profile="nodes", image_tag=ca_tag
    )

    # Umbra makes the constructions of a configtx.yml file based on the policies specified
    # and the configtx base specification.
    # Such configtx specification contains the definition of the profiles to be used
    # by the network to generate the fabric topology artifacts (e.g., genesis.block).
    # In order to fulfill the correct parameters of each profile in configtx, the path
    # of the profiles must be specified, separated by dots. And each of these profiles
    # must be defined with the names of the orgs or orderers that must fill their settings in.
    # Then, umbra understands it must fill the proper path of a configtx profile with
    # the correct information of a org/orderer in order to compose the complete configtx.yml
    # file to create the orgs/orderers/CAs artifacts.
    # In a future release, umbra is planned to detect those configs and make the proper
    # definition of settings in configtx.
    fab_topo.configtx(configtx)
    p1 = "TwoOrgsOrdererGenesis.Consortiums.SampleConsortium.Organizations"
    p2 = "TwoOrgsOrdererGenesis.Orderer.Organizations"
    p3 = "TwoOrgsChannel.Application.Organizations"
    fab_topo.set_configtx_profile(p1, ["org1", "org2"])
    fab_topo.set_configtx_profile(p2, ["orderer"])
    fab_topo.set_configtx_profile(p3, ["org1", "org2"])

    # The interconnection of umbra orgs/orderer to the network must be defined.
    # When a org is connected to a network, all its peers/CAs are connected to the network too.
    fab_topo.add_org_network_link("org1", "s1", profile="links")
    fab_topo.add_org_network_link("org2", "s1", profile="links")
    fab_topo.add_org_network_link("orderer", "s1", profile="links")

    # Defines the resource profiles for nodes and links.
    # The amount of node resources are defined as the maximum number of logical CPUs
    # a node can make use; the amount of memory (MB) the node can utilize, as disk is yet
    # not implemented.
    node_resources = fab_topo.create_node_profile(cpus=1, memory=1024, disk=None)
    # The specification of link resource are defined as bandwidth (MB), delay,
    # and loss (percentage of packet loss, e.g., 0.1 for 10%).
    link_resources = fab_topo.create_link_profile(bw=1, delay="2ms", loss=None)

    # Each node and link in the network can be associated with a resource profile.
    # The names of the profiles are associated with the creation of the node and link
    # resources.
    # I.e., in each node of the network, there was defined the profile="nodes", the line
    # below specified that such profile named "nodes" must have the configuration of
    # resources associated with node_resources, i.e., "cpus=1, memory=1024, disk=None"
    # Similarly the same happens for links, their profiles are defined by the work "links",
    # and in the line below the "links" profile receive the assignment of resource defined
    # by link_resources, i.e., "bw=1, delay="2ms", loss=None".
    fab_topo.add_node_profile(node_resources, profile="nodes")
    fab_topo.add_link_profile(link_resources, profile="links")

    # Save the experiment.
    # When saving, an experiment (topology and events) are properly compiled in a format
    # that umbra later can load and utilize.
    # Saving an experiment means all the topology artifacts are going to be built.
    # In the case of fabric, it means umbra running cryptogen and configtxgen in the built
    # files cryptoconfig.yml and configtx.yml generated by umbra, utilizing the specified
    # fabrictopology components.
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
