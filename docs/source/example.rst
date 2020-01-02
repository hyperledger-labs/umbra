Example
=======

To examplify how umbra can be utilized, an extension was coded to support Hyperledger Fabric v1.4.
The details of how that was coded are exposed in the Extensions section. Here is just the explanation of what the Fabric example realizes.


Building it
***********

Here, it is assumed that the steps mentioned in the Installing section were already followed.

In the root folder named build/ a script named build_fabric.sh downloads and installs all the requirements needed to run the Fabric example.

In the root folder named examples/, the fabric/ folder contains all the requirements needed to build the configuration files to be used by the Fabric example.
The source code in the file build_configs.py realizes all the construction of the needed skeleton of files for the Fabric nodes. 
This file import a class from umbra-configs named FabricTopology and builds the experimental topology using it. 
A file located in the folder base_configtx/ named fabric.py is the source of the policies for organizations and the main configtx file build to create the requirements for the fabric blockchain (e.g., genesis, anchors, channel). 
When the build() function is called upon the FabricTopology instance, all the configurations files needed for the Fabric blockchain network are automatically created. For instance, this includes all the crypto material for all the peers, and the configuration file named fabric_sdk_config.json to be imported by the fabric python SDK when calling the scheduled events to peers in the Fabric blockchain. 
At the end of this file, a configuration is saved based on the Scenario instance created, which has the FabricTopology instance and the events defined accordingly. This configuration file, named config_fabric_simple.json, contains all the hooks for the crypto material, fabric-python-sdk configuration file, and other needed files suchas as the genesis block.  
Executing the file as the commands below, all the requirements are satisfied to execute the Fabric blockchain in Umbra.


``
$ cd umbra/examples/fabric

$ /usr/bin/python3 build_configs.py 

$ cd -
``


Running it
**********

Considering all the execution of the Installing requirements and the build_configs.py file realizing all the requirements for the Fabric blockchain example to be executed by Umbra, now the execution of the Umbra components can be initialized to instantiate the specified Fabric configuration (topology and events).

The executable file named run.sh in the umbra/examples/ folder contains the commands to start/stop the python3 modules umbra-orch and umbra-scenarios, create/remove a management docker network named umbra, and deploy the generated config_fabric_simple.json in umbra-orch.

Having that executed, all the instantiation of components from the saved FabricTopology will take place (i.e., peers, orderers, links, etc) and events will be called on them. 

The commands bellow respectivelly start and stop the example experiment with Fabric.

``
$ sudo -H ./run.sh start -c ./fabric/fabric_configs/config_fabric_simple.json 

$ sudo -H ./run.sh stop
``

In addition, during the execution of the experiment, the command below enters the log screens that each component executes in Umbra.

``
$ sudo -H byobu attach-session -t umbra
``

The program byobu is used to create different windows for tha same session to facilitate the visualization of the logs of the umbra modules.
As the Fabric containers will be initialized, it is also possible to check their logs via the command docker logs (container name), and thus check the execution of the Fabric components.


Modifying it
************

To modify the Fabric experiment, it is just needed to modify the build_configs.py file, changing how the FabricTopology instance is built, besides the events scheduled.
If new orgs are added, the file fabric.py inside base_configtx folder needs to be modified accordingly to define the policies in configtx needed for the creation of the Fabric requirements.
