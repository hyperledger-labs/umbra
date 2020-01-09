Umbra
=====

An emulation platform for Hyperledger blockchains.


The simulation research internship during the summer of 2018 led to the creation of the Hyperledger Umbra Lab. Due to the overall difficulty of getting Hyperledger blockchain frameworks running under the Shadow simulation tool, work on the Umbra lab has slowed to a crawl. A different network emulation tool called Mininet was proposed as an alternative to using Shadow and it has the potential to drastically reduce the startup cost of getting a network emulation tool running Hyperledger blockchains. 


Scope
*****

Umbra is a platform by the means of Mininet and plugins for Hyperledger distributed ledgers so that they can run under emulation in a lab environment.

It is intended to be an ongoing project to provide a research tool for understanding and improving the Hyperledger blockchain platforms as well as for conducting future research in consensus algorithms, scalability, security, etc.


Foundation
**********

* Mininet - http://mininet.org/
* Maxinet - http://maxinet.github.io/
* Containernet - https://containernet.github.io/

Mininet was developed for fast prototyping of emulated programmable networks in a laptop. Later there were different extensions proposed on top of it, such as maxinet enabling experiments in distributed clusters of servers, and containernet enabling the experimentation with Docker containers. Mininet was developed for high fidelity and later on extended to support the features proposed by Maxinet. Containernet was built on top of mininet version 2.2.0, therefore inheriting its most recent enhancements.

Umbra elaborates its architecture on top of the enhancements proposed by containernet. As being evaluated, possible contributions to containernet will be performed in order to enhance it with the most recent features provided by Docker (i.e., current docker-py API) as well as mininet (i.e., currently in version 2.3).


How it Works
************

Umbra works with support of virtualization technologies, containers (Docker) and programmable switches (Open vSwitch). Using containernet it deployes an underlying network which serves as the infrastructure for the blockchain platform of choice (e.g., Iroha, Fabric, Indy, etc) to be executed as the overlay application network. Nodes and links can be configured with resource constraint rules (e.g., cpu, memory, bandwidth, latency, etc). Besides, umbra allows events (e.g., transactions, chaincode invoke, update node/link resources) to be scheduled targeting the blockchain platform using plugins. 

Roadmap
*******

Umbra lives in its childhood, currently developed mostly using the Python 3 programming language.

The road so far:

* Umbra was developed in the Hyperledger Internship 2019 program;
* It contains 3 main modules (umbra-scenarios, umbra-orch, umbra-configs) - see the Architecture section;
* There is support for Fabric v1.4 blockchain project and an example with instructions.

Work ahead:

* Support for other blockchain projects;
* Scale to multiple servers;
* Implement a common dashboard with run-time status of the emulated blockchain network.


FAQ
***

TBD.