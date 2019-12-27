Architecture
============


Design Principles
*****************

Umbra was designed having in mind the following guidance:

* Fast and simple prototypes: with simple APIs it is possible to construct different topologies for blockchain networks be experimented. Those are easily generated in any laptop, enabling deployments in small or large scales.
* Lightweight execution: the source code is easily portable, installed and utilized in multiple underlying environments (e.g., laptop, cloud servers, 
* Transparent reproduction: 

Components
**********

Umbra has three independent modules:

* umbra-configs: defines APIs to implement the topology and events that will be respectively deployed and triggered when testing a blockchain platform. 
* umbra-orch: Mainly 
* umbra-scenarios: 


The prototype will be mainly written in Python 3, having its configuration files written in YAML. The configuration file will be parsed as input to the main management module of the architecture to realize a test. A test will deploy the topology and execute the events programmed in the configuration file. A test scenario will be deployed using the containernet platform. The configuration file will define the structure (i.e., network topology), the set of hyperledger components and their roles running on Docker containers, and specified resource allocations for nodes and links. During the tests, there will be modules performing the stimulus on the topology and its components, modules monitoring the test components and particular topology structures, and modules realizing the analysis of the collected data during the test and after it. Stimulus refers to a set of actions performed by hyperledger nodes, and actions executed on the topology itself (e.g., node/link failures, adjustments in node/link resources). Monitoring refers to the collection of node/link metrics (e.g., cpu percent, packets transmitted, etc) and particular hyperledger events (e.g., transaction confirmation time). Analysis refers to the possible algorithms (e.g., statistics, machine learning) that might be applied over the collected data from monitoring during and after a test.

