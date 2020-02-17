Extending Umbra
===============

In order to explain how umbra was coded to support multiple Hyperledger blockchain projects, this part explains the extensions coded in Umbra to support Fabric. 
As such, this part also illustrates how other blockchain projects can be supported by Umbra.
The extensions are separated by components, and at the end it is showed how to construct a specific example, included the build of requirements needed for that.


umbra/design
************

In umbra/design/configs.py file the major change was due to creating a extension of the Topology class, named FabricTopology. 
As the source of knowledge for Fabric was the tutorial named Building your First Network, such inspiration was translated into an API that could be used to add orgs, orderers and peers that creates multiple configuration files in an automated way.
In general, these configuration files consist of:

* Cryptographic material: all the public/private keys, tls certificates, and other crypto material generated from the binary named cryptogen, which needs a source file (usually named crypto-config.yaml) to output such files. Thus, from the FabricTopology it was needed to create such file, and call cryptogen passing it as parameter. 
* Genesis, Anchors, etc...: all the initial block and channel join anchors used by peers and orderers generated from the binary named configtxgen, which needs a source file (usually named configtx.yaml) to output such files. Thus, from the FabricTopology it was needed to create such file, and call configtxgen passing it as parameter.
* Python SDK settings: all the reference to crypto material and path of them for each component of the Fabric Topology in order to be loaded and used by the fabric-python-sdk when triggering events on the Fabric instantiated topology.
* Scenario Topology: the main configuration file to be used by umbra/broker and umbra/scenario to deploy the actual topology with containers and virtual switches as infrastructure to the Fabric blockchain network. It makes use of a file named fabric.yaml (located at umbra/design/fabric/base) which contains all the base templates for the docker containers executing the images of CAs, orderers and peers. 

Therefore, the FabricTopology class enables the abstracted definition of orgs, peers, CAs and orderers, which are used to build all the configuration files described above. Any changes in the way the Fabric containers are deployed can be done in the fabric.yaml base file. Besides, all the policy definitions used as source of configtx need to be specified when building the topology (in the examples/fabric/base_configtx folder the file fabric.py has such policies defined that are used in the build_configs.py file).


umbra/broker
************

The core of umbra/broker allows it to be extensible to multiple blockchain projects in a plugin manner. In the plugins folder inside umbra/broker, a file named fabric.py contains a class named FabricEvents, which is responsible to interface the fabric-python-sdk and trigger the needed/scheduled events on the instantiated Fabric blockchain network.
This structure of plugins are imported by the Operator component in umbra/broker, and loads all the events according to their category, which references a different blochchain name, in this case plugin.

FabricEvents thus loads the fabric-python-sdk component and uses it to interface the instantiated Fabric components. In order to do so, fabric-python-sdk needs the following files:

* fabric-python-sdk.yaml: the generated file from umbra/design that contains all the reference to the Fabric blockchain components and their crypto material.
* configtx.yaml: the python SDK needs the configtx file in order to load the needed policies to interface the Fabric components.
* chaincode directory: to compile, instantiate and invoke chaincode the python SDK needs to reference a directory where such source code resides.

Multiple interfaces, i.e., functions, to the python SDK can be coded to reference events schedule upon the Fabric Topology. In this case, such events must be clearly and well-defined in umbra/design.
For any other implementations of blockchain projects, interfaces to python SDKs must be implemented similar to the fabric.py plugin file.
And similar to the class FabricEvents, Operator component of umbra/broker must import the coded component and reference the events to be built upon the category of the blockchain project referenced in the events. 


umbra/scenario
**************

The overall interface to Containernet written in the umbra/scenario/environment.py file that was coded to create a umbra management network, assign IP addresses to interfaces of containers, already apply MAC addresses known to all the nodes in the network, and have all of the nodes also known by their DNS names. Those features are available for all blockchain projects, not just Fabric. 
Thus, just enabling the abstractions of nodes and links to construct a topology file to be interpreted by umbra/scenario is the main requirement that umbra/design must detain. 
The Environment class inside the file umbra/scenario/environment.py, parses and translates nodes and links into instantiated containers/switches and links, the parameters for thoses entities can be modified in that class.


build
*****

Each Hyperledger blockchain project, when supported by Umbra, must have its dependencies installed by a build_project.sh file inside the build directory. 
For instance, build/build_fabric.sh containes all the commands to install the Fabric requirements, download the docker images, and install the fabric-python-sdk. 
