Example
=======

To examplify how Umbra can be utilized, an extension was coded to support Hyperledger Fabric v1.4.
The details of how that was coded are exposed in the Extensions section. Here is just the explanation of what the Fabric example realizes.

.. image:: /imgs/imgs/example_fabric_topology.JPG.JPG

Building
********

Here, it is assumed that the steps mentioned in the Installing section were already followed and performed in a host machine.

In the root folder named build/ a script named build_fabric.sh downloads and installs all the requirements needed to run the Fabric example.

In the root folder named examples/, the fabric/ folder contains all the requirements needed to build the configuration files to be used by the Fabric example.
The source code in the file build_configs.py realizes all the construction of the needed skeleton of files for the Fabric nodes (docker containers). 
This file import a class from umbra/design component named FabricTopology and builds the experimental topology using it.
A file located in the folder base_configtx/ named fabric.py is the source of the policies for organizations and the main configtx file build to create the requirements for the fabric blockchain (e.g., genesis, anchors, channel). 
When the build() function is called upon the FabricTopology instance (to save the scenario config), all the configurations files needed for the Fabric blockchain network are automatically created. For instance, this includes all the crypto material for all the peers, and the configuration file named fabric_sdk_config.json to be imported by the fabric python SDK when calling the scheduled events to peers in the Fabric blockchain. 
At the end of this file, a configuration is saved based on the Scenario instance created, which has the FabricTopology instance and the events defined accordingly. This configuration file, named fabric_configs/Fabric-Simple-01.json, contains all the hooks for the crypto material, fabric-python-sdk configuration file, and other needed files such as the genesis block.  
Executing the file as the commands below, all the requirements are satisfied to execute the Fabric blockchain in Umbra.

In the examples/fabric folder, the files/folder structure is described below:

* base_configtx: contains all the source material for the creation of the configtx.yaml file needed by Fabric (e.g., python SDK, configtxgen, etc).
* chaincode: contains source code with examples of chaincode to be executed by the Fabric network on umbra.
* fabric_configs: contains all the skeleton of configuration files to execute Fabric.
* build_configs.py: a python script, making use of umbra/design component, to create Fabric configuration files (placed in fabric_configs) enabling Fabric to be executed by umbra.

Pay attention that in the file fabric_configs/Fabric-Simple-01.json all the nodes (references to docker container templates) already have defined all the environment variables, volumes, commands, etc, that are correctly fulfilled based on all the material generated from building the FabricTopology instance (i.e., crypto keys, certificates, policies).

.. code-block:: bash

    $ cd umbra/examples/fabric

    $ /usr/bin/python3 build_configs.py 

    $ cd -


Running
*******

Considering all the execution of the Installing requirements and the build_configs.py file realizing all the requirements for the Fabric blockchain example to be executed by Umbra, now the execution of the Umbra components can be initialized to instantiate the specified Fabric configuration (topology and events).

The executable file named run.sh in the umbra/examples/ folder contains the commands to start/stop the python3 scripts umbra-broker and umbra-scenario, create/remove a management docker network named umbra, and deploy the generated Fabric-Simple-01.json in umbra-broker.

Having that executed, all the instantiation of components from the saved FabricTopology will take place (i.e., peers, orderers, links, etc) and events will be called on them. 

The commands below respectively start and stop the example experiment with Fabric.

.. code-block:: bash

    $ sudo -H ./run.sh start -c ./fabric/fabric_configs/Fabric-Simple-01.json

    $ sudo -H ./run.sh stop


In addition, during the execution of the experiment, the command below checks the logs that each component executes in Umbra.

.. code-block:: bash

    $ tail -f ./logs/broker.log

    $ tail -f ./logs/scenario.log


As the Fabric containers will be initialized, it is also possible to check their logs via the command docker logs (container name), and thus check the execution of the Fabric components.


Modifying
*********

To modify the Fabric experiment, it is just needed to modify the build_configs.py file, changing how the FabricTopology instance is built, besides changing how the events are scheduled.
If new orgs are added, the file fabric.py inside base_configtx folder needs to be modified accordingly to define the policies in configtx needed for the creation of the Fabric requirements.


Changing environment during runtime
***********************************

We will use the broker's environment plugin (``umbra/broker/plugins/env.py``) to generate event that modifies the environment behavior. Refer `build_configs <https://github.com/hyperledger-labs/umbra/blob/master/examples/fabric/build_configs.py>`_.

Following are example usecases:

.. code-block:: python

	# 1. Kill a container
	ev_kill_container = {
	    "command": "environment_event",
	    "target_node": <peer_name>, # e.g. "peer0.org2.example.com"
	    "action": "kill_container",
	    "action_args": {},
	}

	# 2. Set mem limit
	ev_mem_limit_peer1_org1 = {
	    "command": "environment_event",
	    "action": "update_memory_limit",
	    "action_args": {
	        "mem_limit": <amount_in_bytes>, # e.g. 256000000 for 256MB memory
	        "memswap_limit": -1
	    },
	    "target_node": <peer_name>, # e.g. "peer0.org2.example.com"
	}

	# 3. Set cpu limit. More info at
	# https://docs.docker.com/config/containers/resource_constraints/#cpu
	# https://www.kernel.org/doc/Documentation/scheduler/sched-bwc.txt
	ev_cpu_limit_peer1_org2 = {
	    "command": "environment_event",
	    "target_node": <peer_name>, # e.g. "peer0.org2.example.com"
	    "action": "update_cpu_limit",
	    "action_args": { # refer Docker docs for these values
	        "cpu_quota": 10000,
	        "cpu_period": 50000,
	        "cpu_shares": -1,
	        "cores": {}
	    },
	}

	# 4. Update link resources
	# Here, we change the resources of s0<-->peer1.org1 interface
	# to bandwidth of 3Mbps, with 4ms delay, and packet loss rate of 10%
	ev_update_link_res = {
	    "command": "environment_event",
	    "action": "update_link",
	    "action_args": {
	        "events": [
	            {
	                "group": "links",
	                "specs": {
	                    "action": "update",
	                    "online": True,
	                    "resources": {
	                        "bw": 3, # Mbps
	                        "delay": "4ms",
	                        "loss": 10, #
	                    }
	                },
	                "targets": ("s0", "peer1.org1.example.com")
	            },
	        ]
	    },
	}

	# 5. Change link state, e.g. UP or DOWN
	# Beginning of test all link should be up.
	# Set the "online" key to either True or False
	# Example below set the orderer interface to DOWN
	ev_update_link_orderer_down = {
	    "command": "environment_event",
	    "action": "update_link",
	    "action_args": {
	        "events": [
	            {
	                "group": "links",
	                "specs": {
	                    "action": "update",
	                    "online": <True|False>, # True=UP, False=DOWN
	                    "resources": None
	                },
	                "targets": ("s0", "orderer.example.com")
	            },
	        ]
	    },
	}


Creating stimulus in the network via agent
******************************************

`umbra-agent` currently supports `ping` to send ICMP echo, `iperf` to simulate heavy traffic, and `tcpreplay` to replay pcap packet. Only `ping` is tested thus far, other examples coming soon.

.. code-block:: python

	# Ping peer0.org1.example.com at 1 packet per second
	# for 4 seconds
	ev_agent_ping_peer0org1 = {
	    "agent_name": agent_name,
	    "id": "100",
	    "actions": [
	        {
	            'id': "1",
	            "tool": "ping",
	            "output": {
	                "live": False,
	                "address": None,
	            },
	            'parameters': {
	                "target": <target_node>, # e.g. "peer0.org1.example.com"
	                "interval": "1",
	                "duration": "4",
	            },
	            'schedule': {
	                "from": 1,
	                "until": 0,
	                "duration": 0,
	                "interval": 0,
	                "repeat": 0
	            },
	        },
	    ],
	}

