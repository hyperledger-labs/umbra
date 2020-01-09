Installing
==========

Prerequisites
*************

Currently, Umbra is developed and tested on Ubuntu 18.04.

There are no strict requirements of hardware for Umbra. It will depend on the size of the network that's being tested, and the configuration of resources to be allocated for nodes and links. 
Therefore, Umbra can be installed and run in different machine configurations, the need of specific hardware specs will depend on the use case being evaluated, which must be correctly dimensioned using the resource constraints for nodes and links available in Umbra.

The main modules of Umbra require versions 2 and 3 of python (this is being changed to python3 only!). All the other requirements can be checked in the build scripts as described below. In general, Umbra uses apt, git and pip to install its requirements.


Main Modules
************

Each one of Umbra main components is a different python module. 
All their requirements are installed together with them by the build.sh script inside the build folder.
The steps below contain the Umbra installation commands.

``
$ git clone https://github.com/hyperledger-labs/umbra/

$ cd umbra/build

$ sudo chmod +x build.sh

$ sudo ./build.sh

$ cd -
``

When executing this script, it will install all the Umbra python modules and their dependencies, and it will install containernet and its requirements.


Requirements for Blockchains
****************************

Umbra was designed to support multiple blockchains, so in an independent way each blockchain platform when supported has its own build files also inside the build folder. As such, for each blockchain platform there will be a installation script inside the build folder.
For instance, as Umbra supports Hyperledger Fabric v1.4, installing the requirements to execute Fabric on Umbra can be done with the steps below.

``
$ cd umbra/build

$ sudo chmod +x build_fabric.sh

$ sudo ./build_fabric.sh

$ cd -
``

When executing this script, it will install the fabric-python SDK, download all the Fabric docker images, modify them accordingly to enable support for containernet functionalities (i.e., they must have the packages net-tools and iproute2 installed on them), and add the binaries configtxgen and cryptogen to the PATH env variable (i.e., as they are required by the fabric-python-sdk, and the umbra-configs module).
