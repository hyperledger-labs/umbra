# Hyperledger Umbra

An emulation platform for Hyperledger blockchains.

This lab is intended to be an ongoing project to provide a research tool for understanding and improving the Hyperledger blockchain platforms as well as for conducting future research in consensus algorithms and scalability. This lab is not intended to be a shipping product but rather an ongoing collaboration between academic, corporate, and hobbyist researchers improving upon existing capabilities and also trying new things with Hyperledger blockchains.

This project is the outcome of the 2019 and 2020 Hyperledger internship projects (e.g., [Hyperledger-Labs Umbra](https://wiki.hyperledger.org/display/INTERN/Hyperledger+Umbra%3A+Simulating+Hyperledger+Blockchains+using+Mininet)).


# Requirements

Umbra is developed and tested in Ubuntu 20.04.

The hardware requirements needed for umbra will depend on the scale of the experiments to be played with it (e.g., number of nodes in a blockchain topology, amount of events triggered into the topology, the topology resource settings, etc).
For a simple setup its recommended to have available at least: 4 logical cpu cores, 8 GB of RAM, and 10GB of storage.

To begin with umbra there is the need to only install the git and make packages. All the python packages needed by umbra are listed in the file requirements.txt. The other requirements for each blockchain project can be properly installed later.

```bash
sudo apt install git make
```


# Installing

First of all, obtain the umbra source code.

```bash
git clone https://github.com/hyperledger-labs/umbra
cd umbra
```

Given the installation of the umbra requirements, the command below will install umbra.

```bash
sudo make install
```

Umbra can also be installed using a Vagrant virtual machine, either using qemu-kvm/libvirt or virtualbox as providers, as stated below:

```bash
sudo make vagrant-run-libvirt # Installs umbra in a virtual machine using qemu-kvm/libvirt, and turn it on
sudo make vagrant-run-virtualbox # Installs umbra in a virtual machine using virtualbox, and turn it on
```

As any other Vagrant virtual machine (box), it is possible to interact with it via vagrant commands, such as using ssh to login (i.e., vagrant ssh). Notice the amount of resources allocated for the umbra virtual machine in the Vagrantfile, you can customize it if you need. Besides, the network created by umbra and the virtual machine IP address must be noted when experimenting with examples that use remote environments (scale umbra to multiple servers and/or virtual machines).


# Installing the Blockchains Dependencies

Currently umbra supports Fabric and Iroha projects. Installing the dependencies for Fabric and/or Iroha is needed to run their respective examples.

**Important:** umbra supports Fabric 2.0+, however the scheduling of events using the fabric-python-sdk is not yet supported, because fabric-python-sdk does not support Fabric 2.0+ yet, as soon it does umbra will be updated too. Support for Fabric 1.4 is discontinued in umbra, so you can use umbra to deploy a network with Fabric 2.0+ and interact with it using another Fabric SDK. 

To install the Fabric dependencies (download docker images, install the fabric-python-sdk, and the binaries configtxgen and cryptogen):

```bash
make install-fabric
```

To install the Iroha dependencies (download docker images, install the iroha-python-sdk):

```bash
make install-iroha
```

# Examples

Having umbra installed, it is possible to experiment with it using the provided examples, inside examples/ folder.

The README.md file in the examples folder provide the instructions to experiment with umbra.

Inside the configuration files of the examples, the comments provide guidelines on how to understand and compose your own umbra experiments.


# Umbra: Architecture and Workflows

Umbra contains the following components:
- **umbra-design:** it is not properly a component, however a API that allows users to compose experiments for umbra. An experiment in umbra-design is designed to have a main instance of the blockchain project as a Topology (e.g., FabricTopology, IrohaTopology, etc) and events associated with the topology. The topology provides abstractions of the blockchain project (e.g., how to add nodes, links, etc). And the events provide means to interact with the instantiated topology, nodes/links status and resources, and with the blockchain itself, via its SDK project.

- **umbra-scenario:** it is a component that consumes Containernet (Mininet) APIs to properly interact (instantiate, tear-down, modify, etc) with the topology (containers, links, switches). The umbra-scenario can have its instances deployed in multiple servers (in umbra these are called environments) so it can enable umbra to be deployed at scale.

- **umbra-broker:**
- **umbra-monitor:**
- **umbra-agent:**
- **umbra-cli:**

The workflow, a day in umbra's shoes, is described in the steps below:
1. 

# License

Hyperledger Umbra software is released under the Apache License Version 2.0 software license. See the [license file](LICENSE) for more details.

Hyperledger Umbra documentation is licensed under the Creative Commons Attribution 4.0 International License. You may obtain a copy of the license at: http://creativecommons.org/licenses/by/4.0/.

# Contact

If you have any issues, please use GitHub's [issue system](https://github.com/hyperledger-labs/umbra/issues) to get in touch.

## Mailing-list

If you have any **questions**, please use the hashtag #umbra in the subject of emails to the hyperledger labs mailing list: labs@lists.hyperledger.org.

## Contribute

Your contributions are very welcome! Please fork the GitHub repository and create a pull request.

## Lead Developer

Raphael Vicente Rosa
* Mail: <raphaelvrosa (at) gmail (dot) com>
* GitHub: [@raphaelvrosa](https://github.com/raphaelvrosa)
* Website: [INTRIG Webpage](https://intrig.dca.fee.unicamp.br/raphaelvrosa/)

This project is part of [**Hyperledger Labs**](https://www.hyperledger.org/blog/2018/01/23/introducing-hyperledger-labs).

# Acknowledgements

This project is idealized and greatly supported by:
- David Huseby - <dhuseby (at) linuxfoundation (dot) org>