# Hyperledger Umbra

An emulation platform for Hyperledger blockchains.

This lab is intended to be an ongoing project to provide a research tool for understanding and improving the Hyperledger blockchain platforms as well as for conducting future research in consensus algorithms and scalability. This lab is not intended to be a shipping product but rather an ongoing collaboration between academic, corporate, and hobbyist researchers improving upon existing capabilities and also trying new things with Hyperledger blockchains.

This project is the outcome of the 2019 and 2020 Hyperledger internship projects (e.g., [Hyperledger-Labs Umbra](https://wiki.hyperledger.org/display/INTERN/Hyperledger+Umbra%3A+Simulating+Hyperledger+Blockchains+using+Mininet)).


# Requirements

Umbra is developed and tested in Ubuntu 20.04.

The hardware requirements needed for umbra will depend on the scale of the experiments to be played with it (e.g., number of nodes in a blockchain topology, amount of events triggered into the topology, the topology resource settings, etc).
For a simple setup its recommended to have available at least: 4 logical cpu cores, 8 GB of RAM, and 10GB of storage.

To begin with umbra there is the need to only install the make package. All the python packages needed by umbra are listed in the file requirements.txt. 

```bash
sudo apt install make
```


# Installing

First of all, obtain the umbra source code.

```bash
git clone https://github.com/raphaelvrosa/umbra
cd umbra
```

Given the installation of the umbra requirements, the commands below install umbra.

```bash
sudo make install
```

Umbra can also be installed using a Vagrant virtual machine, either using qemu-kvm/libvirt or virtualbox as providers, as stated below:

```bash
sudo make vagrant-run-libvirt # Installs umbra in a virtual machine using qemu-kvm/libvirt, and turn it up
sudo make vagrant-run-virtualbox # Installs umbra in a virtual machine using virtualbox, and turn it up
```

As any other Vagrant virtual machine (box), it is possible to interact with it via vagrant commands, such as using ssh to login (i.e., vagrant ssh).


# Running

Having umbra installed, it is possible to experiment with it using the provided examples, inside examples/ folder.

The README.md file in the examples folder provide the instructions to experiment with umbra.

Inside the configuration files of the examples, the comments provide guidelines on how to compose umbra experiments.


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