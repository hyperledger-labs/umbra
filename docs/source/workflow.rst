Workflow
========


Use Case View
*************

There exists two roles in the umbra use case view, the blockchain Tester and the Analyst/Viewer.
Using the provided APIs, a Tester defines the configuration file, uses it to perform the test in a target execution environment, and collects the experimental data metrics and logs (raw and analyzed) output of the monitoring functions. An Analyst just visualizes and performs analysis on the test results. Visualization of test results can be triggered during the execution of the test and after it. So an Analyst might visualize tests metrics in runtime via plugins (e.g., grafana, kibana, 
The examples are meant to be fully automated, but Testers might interact with the running topology during the tests too.


Logical View
************

Using an API provided by umbra-configs, a tester codes the scenario needed for an experiment, the output of such scenario is a configuration file in a yaml format. 
A run script starts the applications modules umbra-orch and umbra-scenarios, both detaining a REST API. 
The yaml (config) file is sent via an http rest api to the umbra-orch component which parses it, sends the scenario topology to umbra-scenarios via an http rest api, which is deployed. Acknowledging the deployment by a message received from umbra-scenarios, umbra-orch triggers the events specified in the yaml (config) file. These events interface the management APIs of the running blockchain components via their SDK (e.g., fabric-python-sdk interacting with Fabric peers/cas/orderers).
At the end of events, the tester can finish the execution of the scenarios and the running modules and collects the metrics measured during the experiment.

As such, for each main umbra module the following logic describes the most important classes, their organization and the most important use case realizations.

* umbra-configs

    * Graph:
    * Topology:

* umbra-orch

    * Manager:
    * Operator:

* umbra-scenarios
    
    * Experiment:
    * Scenario:

Flow View
*********

How it is going to work: the configuration file is parsed and converted into an internal data structure that is used to instantiate the specified topology. Executed the topology, the events specified in the configuration file take place. During the test, monitoring functions collect metrics to be shown in graphics online. After the test, the analysis of the whole monitored data is analyzed and a report is generated containing the test life cycle (i.e., status involving the phases of pre-deployment, execution, and post-mortem).

1. The Tester defines the experiment configuration that will be executed. It contains the whole lifecycle of the structural (topology/infrastructure) and functional (events/visualization) definitions.
2. Given such configuration to the Manager component, it will execute the parsing of the configuration, set all the deployment configuration to be deployed.
3. A Topology component will deploy the given configuration file, creating the Containernet network. It will send back to Manager the management information of the deployed components. Such information contains among other settings, the IP address of the management interface of the containers deployed in the network.
4. Manager will start triggering the scheduled events (defined in the Experiment Configuration) to take place in the infrastructure and/or topology.
5. In addition, the Tester can utilize the Manager interface to trigger events during the execution of the experiment.
6. The Operator component then parses such event requests and schedule their occurrence in the topology and/or infrastructure.
7. Events take place, e.g.: containers running hyperledger project components start/stop mining, links/nodes fail/restore or have resources changed, metrics are monitored from infrastructure perspective, etc.
8. Metrics, output of events execution, are received in Operator. The set of events-metrics pairs are pushed to Manager, and possibly a Visualization component.
9. Metrics are displayed in different graphic formats according to the pushed instructions.
10. Given the schedule of the Experiment Configuration or a request from the Tester, Manager stores all events-metrics, and request the end of the topology/infrastructure components.
11. All the components are stopped and removed, leaving the infrastructure as it was before the experiment started.
12. Acknowledged the end of the infrastructure/topology execution, Manager outputs a Experiment report containing the comprehensive set of events and their collected metrics during the whole experiment.
13. Tester receives the output report and possibly send it to an experiment Analyst/Viewer.



Deployment View
***************

In general, the project code can be installed in one or more servers interconnected by a common network, composing a cluster. In one server, specified as the jump server, the main modules of the project load the configuration file and execute the experiments.


Directory Structure
*******************

* build: contains the installation scripts for all the umbra modules, in addition to the scripts needed to install the dependencies for the blockchain platforms be executed by umbra.
* docs: all the documentation is stored in docs, included all the source files (.rst) needed to compile the html pages for readthedocs.
* examples: contains a README file on how to run umbra examples, and for each example it contains a folder referencing the name of the blockchain platform containing instructions and all the scripts needed to run the example.
* umbra-orch: contains all the module source code to install and run the orchestration logic of umbra, i.e., how to receive a scenario configuration request, deploy it and trigger the events programmed in the scenario logic. umbra-orch contains plugins, each one specified for a different blockchain platform it supports.
* umbra-configs: contains all the module source code to install and enable APIs for the configuration logic of umbra, i.e., how to specify different topology APIs to build the configuration needed for each blockchain platform to be executed by umbra-orch. 
* umbra-scenarios: contains all the module source code to install and run the plugin that enables containernet to deploy the topology needed to execute a blockchain platform. 