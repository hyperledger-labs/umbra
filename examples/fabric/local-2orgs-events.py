import os
import logging

# First of all, import from umbra-design the configs that
# refer to the construction of your Experiment using the
# FabricTopology API.
from umbra.design.configs import Experiment, FabricTopology

# Then, import the configtx definitions, which are going
# to be used by each one of the orgs policies, and also
# for the whole construction of the configtx.yml file.
# Each experiment/topology can have its own configtx custom definitions.

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
    fab_topo = FabricTopology("local-2orgs-events", chaincode_dir=chaincode_dir)

    # Defines experiment containing topology, later events can be added.
    # An experiment consists of a topology and events. It sets the ground for
    # what is going to actually be instantiated and executed.
    experiment = Experiment("local-2orgs-events")
    experiment.set_topology(fab_topo)

    # Environments in umbra are the places (i.e., baremetal servers and/or virtual machines)
    # where the components of umbra are executed, and consequently the topology itself.
    # An environment can be remote or local (parameter remote set to true or false).
    # The user must be allowed to execute operations as sudo in the environment.
    # In a local environment the user will be the logged in user that used to instantiate and run umbra.
    # By default, umbra defines for its topologies the umbra-default environment,
    # meaning all the components will be executed in the host machine, using the localhost address.

    # Umbra realizes a network is associated with an environment, and it realizes
    # all the nodes interconnected to this network are also in the same environment
    # as the network. All the proper settings regarding the reachability of
    # the nodes, network, environment is handled by umbra.

    # The network must be associated with the environment where it is going
    # to be placed/executed. All the nodes connected to the network will be deployed
    # in the environment where the network is placed.
    fab_topo.add_network("s1", envid="umbra-default")

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
    fab_topo.add_org_network_link("org1", "s1", "links")
    fab_topo.add_org_network_link("org2", "s1", "links")
    fab_topo.add_org_network_link("orderer", "s1", "links")

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


    # Events are used to interact with the topology. 
    # Events can be of scenario category when related to modifications
    # that might happen in run-time with the deployed topology, be its nodes and/or links.
    # In the case of a scenario event it must contain the specific group (nodes or links)
    # that its target belongs to. 
    # A target is the reference name to the node (full name) or link (src and dst in any order).
    # The event specs contains the details about the event.
    # For now in the specs of a scenario event, the action can be only update (later add/remove will be added too).
    # In specs: online means if the node/link will be up or down; resources mean the definition of resource the 
    # node or link will have.
    # In links group, a link might have resources specified as bw (bandwidth Mbps), delay (string with number and unit)
    # and loss (packet loss ration as percentage 0-100).
    # In nodes group, a node might have resources specified as docker allows, to have a complete list
    # see https://docs.docker.com/engine/reference/commandline/update/
    # or API docs: https://docker-py.readthedocs.io/en/stable/api.html#module-docker.api.container
    # examples of node resources are: blkio_weight, cpu_period, cpu_quota, cpu_shares, cpuset_cpus,
    # cpuset_mems, mem_limit, mem_reservation, memswap_limit, kernel_memory, restart_policy
    # When the action update is taken on a node, its is not actually stopped or started, it is 
    # paused and unpaused (i.e., all its processes are paused or resumed).
    ev_scenario_01 = {
        "group": "links",
        "specs": {
            "action": "update",
            "online": True,
            "resources": {
                "bw": 3,
                "delay": "4ms",
                "loss": 1,
            },
        },
        "target": ("s1", "peer0.org1.example.com"),
    }

    ev_scenario_02 = {
        "group": "nodes",
        "specs": {
            "action": "update",
            "online": False,
            "resources": {},
        },
        "target": "peer0.org1.example.com",
    }

    ev_scenario_03 = {
        "group": "nodes",
        "specs": {
            "action": "update",
            "online": True,
            "resources": {},
        },
        "target": "peer0.org1.example.com",
    }

    # Events are scheduled by the moment umbra-broker receives the confirmation
    # the topology was successfully instantiated by umbra-scenario, it means time 0.
    # From 0 on all events can be scheduled with the from keyword.
    # The scheduling can take place with other keywords (all integers) too:
    # e.g., sched = {"from": 0, "until": 0, "duration": 0, "interval": 0, "repeat": 0}
    # from is the time when the event must be triggered (0-...)
    # untill is the time the event stops
    # duration is the total duration of time the event must be executed
    # interval is the time the event must wait until its trigger is repeated
    # repeat is the amount of times the event must be triggered
    # For instance:
    # e.g., sched = {"from": 0, "until": 10, "duration": 2, "interval": 1, "repeat": 3}
    # The sched above will start the event in moment 0, repeat the event 3 times, waiting
    # 1 second between each repeatition, have the event last no more than 2 seconds, until
    # all the previous time summed reach 10 seconds. If the event finished before 2 seconds, 
    # that's all fine.
    # Summed, it has 2 (duration) x 3 (repeat) + 1 (interval) x (3 repeat) = 9 seconds 
    # It will finish before the until 10 seconds is reached.
    # The repeatitions stop when until timeout is reached.
    sched_ev_01 = {"from": 2}
    sched_ev_02 = {"from": 10}
    sched_ev_03 = {"from": 20}

    # Events are added by category.
    # scenario refers to infrastructure/umbra-scenario events (nodes/links up/down 
    # and resource updates)
    # Other categories include blockchain models events. Meaning, fabric, iroha, indy, etc.
    # The proper definition of the event must exist for each one of the blockchain projects.
    # The events are defined according to the broker plugins. 
    # In broker, a plugin is a extension that gives support to the events that a python SDK 
    # of a particular blockchain project is consumed. 
    # In local-4orgs-events.py example there are examples of fabric events.
    experiment.add_event(sched=sched_ev_01, category="scenario", event=ev_scenario_01)
    experiment.add_event(sched=sched_ev_02, category="scenario", event=ev_scenario_02)
    experiment.add_event(sched=sched_ev_03, category="scenario", event=ev_scenario_03)

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
