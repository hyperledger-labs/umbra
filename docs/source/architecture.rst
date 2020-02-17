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

Umbra has three independent components:

* design: defines APIs to implement the topology and events that will be respectively deployed and triggered when testing a blockchain platform. 
* broker: main component, responsible for the orchestration and management of the scenario (topology and events)  
* scenario: the actual interface that deploys the topology (i.e. network, containers, virtual switches)
