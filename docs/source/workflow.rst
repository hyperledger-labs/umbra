Views
=====


Use Case View
*************

There exists two roles in the umbra use case view, the blockchain Tester and the Analyst/Viewer.
Using the provided APIs (by umbra/design), a Tester defines the configuration file, uses it (with umbra/broker) to perform the test in a target execution environment (by umbra/scenario), and collects the experimental data metrics and logs (raw and analyzed) output of the logged activities. 
An Analyst just visualizes and performs analysis on the test results. Visualization of test results can be triggered during the execution of the test and after it. So an Analyst might visualize tests metrics in runtime via plugins (e.g., grafana, kibana, plots). 
The experiments are meant to be fully automated, but Testers might interact with the running topology during the tests too.


Logical View
************

Using an API provided by umbra/design, a tester codes the scenario needed for an experiment, the output of such scenario is a set of configuration files. 
A script starts the applications components umbra-broker and umbra-scenario, both detaining gRPC services.
The scenario (config) file is sent to the umbra-broker component which parses it, sends the scenario topology to umbra-scenario, which is deployed. Acknowledging the instantiated topology by a message received from umbra-scenario, umbra-broker triggers the events scheduled in the scenario config file. These events interface the management APIs of the running blockchain components via their SDK (e.g., fabric-python-sdk interacting with Fabric peers/CAs/orderers).
At the end of events, the tester can finish the execution of the scenarios and the running components and checks the logs of the executed components, collecting the needed information.

As such, for each main umbra component the following logic describes the most important classes, their organization and the most important use case realizations.

* umbra/design

    * Graph: defines the inner structure for Topology, a graph that can be used by different graph algorithms via the python3 networkx library.
    * Topology: is a graph that contains nodes and links with profiles assigned. Profiles define resource constraints to nodes (i.e., cpu and memory) and links (i.e., bandwidth, delay, loss). 
    * Events: defines a set of events, each one defined by a category, when (schedule timestamp to be triggered), and parameters. Events are intended to have other fields, specially for scheduling (e.g., duration, repeatitions, until).
    * Scenario: joins a Topology with Events.

* umbra/broker

    * Broker: implements the gRPC interface for umbra-broker, enabling the types of messages it can handle and their callbacks, included interfaces to an instance of Operator.
    * Operator: defines all the interfaces to call the deployment of a topology, and schedule events to be triggered after the instantiation of an experiment.

* umbra/scenario
    
    * Environment: sets the main component that interfaces Containernet APIs to instantiate containers, virtual switches, interconnect them, and assign resources to them.
    * Scenario: implements the gRPC interface for umbra-scenario, creating Environment(s) as requested and interfacing the infrastructure deployed according to requested events (e.g., update nodes/links resources).


Flow View
*********

How it works in summary: a configuration file is parsed and converted into an internal data structure that is used to instantiate the specified topology. Executed the topology, the events specified in the configuration file take place. During the test, monitoring functions might collect metrics to be shown in graphics online. After the test, the analysis of the whole monitored data is analyzed and a report is generated containing the test life cycle (i.e., status involving the phases of pre-deployment, execution, and post-mortem).

1. The Tester defines the scenario configuration that will be executed. It contains the whole lifecycle of the structural (topology/infrastructure) and functional (events/visualization) definitions. This is done via APIs specified by the umbra/design component.
2. Given such configuration to the umbra-broker component, it will execute the parsing of the configuration, set all the deployment configuration to be deployed.
3. A Environment class instance in umbra-scenario will deploy the given configuration file, creating the Containernet network. It will send back to Broker the management information of the deployed components. Such information contains among other settings, the IP address of the management interface of the containers deployed in the network.
4. Broker will start triggering the scheduled events (defined in the Scenario configuration file) to take place in the infrastructure and/or topology.
5. In addition, the Tester can utilize the Manager interface to trigger events during the execution of the experiment.
6. The Operator component of Broker then parses such event requests and schedule their occurrence in the topology and/or infrastructure.
7. Events take place, e.g.: containers running hyperledger project components start/stop mining, links/nodes fail/restore or have resources changed, metrics are monitored from infrastructure perspective, etc.
8. Metrics, output of events execution, are received in Operator. The set of events-metrics pairs are pushed to Broker, and possibly a Visualization component.
9. Metrics are displayed in different graphic formats according to the pushed instructions.
10. Given the schedule of the Experiment Configuration or a request from the Tester, Manager stores all events-metrics, and request the end of the topology/infrastructure components.
11. All the components are stopped and removed, leaving the infrastructure as it was before the experiment started.
12. Acknowledged the end of the infrastructure/topology execution, Broker outputs a Scenario status report containing the comprehensive set of events and their collected metrics during the whole experiment.
13. Tester receives the output report and possibly send it to an experiment Analyst/Viewer.



Deployment View
***************

In general, the project code can be installed in one or more servers interconnected by a common network, composing a cluster. In one server, specified as the jump server, the main components of the Umbra project load the configuration file and execute the experiments.

For now, Umbra runs in a single server. Evolving the project, in the future a single jump server will trigger the execution of Umbra in multiple servers.


Directory Structure
*******************

* **build**: contains the installation scripts for all the Umbra components, in addition to the scripts needed to install the dependencies for the blockchain platforms be executed by Umbra.
* **docs**: all the documentation is stored in docs, included all the source files (.rst) needed to compile the html pages for readthedocs.
* **examples**: contains a README file on how to run umbra examples, and for each example it contains a folder referencing the name of the blockchain platform containing instructions and all the scripts needed to run the example.
* **umbra/common**: contains all the common application models (i.e., protocol buffer messages and services) implemented to be used by the other Umbra components.
* **umbra/broker**: contains all the component source code to install and run the orchestration logic of umbra, i.e., how to receive a scenario configuration request, deploy it and trigger the events programmed in the scenario logic. The executable umbra-broker contains plugins, each one specified for a different blockchain platform it supports.
* **umbra/design**: contains all the component source code to install and enable APIs for the configuration logic of umbra, i.e., how to specify different topology APIs to build the configuration needed for each blockchain platform to be executed by umbra-broker. 
* **umbra/scenario**: contains all the component source code to install and run the plugin that enables Containernet to deploy the topology needed to execute a blockchain platform.
* **umbra/agent**: contains source code related to umbra-agent executable
* **umbra/monitor**: contains source code related to umbra-monitor executable
