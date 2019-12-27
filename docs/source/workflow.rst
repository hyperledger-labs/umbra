Workflow
========


Use Case View
*************

The tests are meant to be fully automated. However Testers might interact with the running topology during the tests too. A Tester defines the configuration file, performs the test in a target execution environment, and collects the experimental data (raw and analyzed) output of the monitoring functions. A Viewer/User just visualizes and performs analysis on the test results. Visualization of test results can be triggered during the execution of the test and after it.


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

Shows how the project components can be deployed in an execution environment. In general, the project code can be installed in one or more servers interconnected by a common network, composing a cluster. In one server, specified as the jump server, the main modules of the project load the configuration file and execute the experiments.


Directory Structure
*******************