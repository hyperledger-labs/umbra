Architecture
============


Design Principles
*****************

Umbra was designed having in mind the following guidance:

* Fast and simple prototypes: with simple APIs it is possible to construct different topologies for blockchain networks to be experimented. Those are easily generated in any laptop, enabling deployments in small or large scale.
* Lightweight execution: the source code is easily portable, installed and utilized in multiple underlying environments (e.g., laptop, cloud servers, etc). 
* Transparent reproduction: configuration files are recipes to be shared and executed in different environments for comparability among experiments, enabling reproducible research.

Components
**********

Umbra has five independent components:

* design: defines APIs to implement the topology and events that will be respectively deployed and triggered when testing a blockchain platform. 
* broker: main component, responsible for the orchestration and management of the scenario (topology and events)
* scenario: the actual interface that deploys the topology (i.e. network, containers, virtual switches)
* agent: runs as one of the "peer" in the blockchain network. It can be used to generate stimulus to the network like interrupting a running blockchain transaction (via ``iperf``) and replay packets (via ``tcpreplay``).
* monitor: runs on the host machine. Used to monitor the status/metrics of both host and containers
