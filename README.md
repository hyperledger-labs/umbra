# Hyperledger Umbra

An emulation platform for Hyperledger blockchains.

This lab is intended to be an ongoing project to provide a research tool for understanding and improving the Hyperledger blockchain platforms as well as for conducting future research in consensus algorithms and scalability. This lab is not intended to be a shipping product but rather an ongoing collaboration between academic, corporate, and hobbyist researchers improving upon existing capabilities and also trying new things with Hyperledger blockchains.

This project is the outcome of the 2019 and 2020 Hyperledger internship projects (e.g., [Hyperledger-Labs Umbra](https://wiki.hyperledger.org/display/INTERN/Hyperledger+Umbra%3A+Simulating+Hyperledger+Blockchains+using+Mininet)).

Umbra is well described in a [Hyperleder Webinar](https://www.youtube.com/watch?v=Aw3AjGiNPF8).

Currently, umbra documentation is being updated, so for now please do not consider the docs inside umbra readthedocs, those are deprecated/old ones.

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

- **umbra-broker:** consists of the core component of umbra, it realizes the coordination of messages among the other components (e.g., to deploy a topology in umbra-scenario, to start umbra-monitor to extract measurements in an environment, or to call blockchain SDK events). 

- **umbra-monitor:** defines the element that monitors the host environment and the topology nodes (i.e., containers). It extracts different metrics from them, sending them to umbra-broker, which parses those metrics and insert them into a database (influxdb) to be shown in graphics (graphana).

- **umbra-agent:** it is an ongoing work, it is designed to be added to the instantiated topology in order to cause anomalies in the network (e.g., consume cpu resources, trigger network traffic congestion, and in the future possibly it can behave as a malicious blockchain node).

- **umbra-cli:** it is the component that automates the experiments of umbra, realizing the installation and instantiation of all the needed components in one or multiple environments and interfaces those components to experiment with them. With umbra-cli one can load an experiment configuration, install umbra in the environments, start the components and trigger the topology instantiation so as its events, similarly it can uninstall umbra and stop components in environments too. 

In a short story, a user composes an experiment using umbra-design APIs, it starts umbra-cli and loads that experiment configuration file on it. Using umbra-cli the user can install umbra in the experiment environments, start the components on them. After that, a user can trigger the instantiation of the topology and the trigger of the experiment events, meanwhile, a monitor component will be instantiated in each environment, sending metrics of the host and the containers (i.e., blockchain nodes deployed by umbra). Those metrics are received by umbra-broker and ploted in graphana after inserted to influxdb. After finishing the experiment, using umbra-cli a user can stop the components and uninstall umbra from all the environments defined in the experiment. 

Each blockchain node (e.g., a fabric peer, or a iroha node, etc) in umbra is instantiated as a docker container, containers are interconnected with virtual switches, an abstraction called network by umbra. When running in multiple environments (i.e., servers) the instances of umbra-scenario in each environment interconnect with each other via GRE tunnels. This provides the notion that every node in the whole network belongs to the same broadcast domain (i.e., layer 2 domain). Umbra makes easy to compose blockchain networks in any size and in different environments, generating and installing all the dependencies needed transparently to the user.


The workflow, a day in umbra's shoes, is described in the steps below:
1. Every experiment starts with the composition of itself, using umbra-design APIs. See the examples folder for more information about, some examples there are commented, so it is possible to understand them and start creating your own experiments.
2. After that, a user can start umbra-cli (see the README in the examples folder) to perform interactions with umbra. With umbra-cli, the user can load the experiment configuration.
3. When triggering the install command inside the cli, umbra-cli is going to recognize each environment settings, defined by the loaded experiment configurationo file, and install umbra and the needed components to execute the blockchain topology. For instance, if the experiment refers to a Iroha topology, umbra-cli is going to install all the Iroha dependencies for umbra to enable the proper execution of the Iroha nodes.
4. Together with the installation, umbra-cli also performs the copy of the crypto material, or accessory files (e.g., genesis block) to each environment, so blockchain nodes (i.e., containers) can have their correct set of volumes mounted on them and their internal configuration available to start their blockchain software components.
5. Triggerint the start command in umbra-cli, the user will notice that in each environment all the needed umbra components will be started. For instance, it is mandatory to have umbra-scenario and umbra-monitor components in each environment, while just a single umbra-broker can synchronize and coordinate all the other components.
6. Triggering the begin command in umbra-cli, it will send the experiment configuration to umbra-broker, which will call each umbra-scenario to start its part of the topology in its own environment, and also to start each umbra-monitor component to send host/container metrics back to it. After acknowledged the topology deployments, umbra-broker will trigger the events in the topology.
7. In the umbra-cli console the user will notice ok or error messages, signaling the correct or wrong execution of the topology and/or events. In each environment logs of the components are placed in /tmp/umbra/logs, so the user can debug the errors.
8. Finally, the user can call end, so umbra-cli send a sign to umbra-broker to required the tear-down of the topology in each environment. This will also make umbra-broker send a sign to umbra-monitor components to stop monitoring hosts/containers in their environment.
9. After that the user can trigger the stop command, so all the umbra components in the experiment environments be stopped.
10. And finally if needed, the user can call the uninstall command in the umbra-cli console, so umbra and its blockchain dependencies are uninstalled from the environments. With a <ctrl+d> command the user exits the umbra-cli console.


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