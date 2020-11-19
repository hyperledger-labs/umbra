# Umbra Examples

This directory contains the source code that defines examples of how to interact with umbra.

If you have already installed umbra (container, virtual machine, baremetal) you can proceed with the following steps.

## Creating the configurations

In each folder, referencing a project name (e.g., fabric, iroha, etc), there are auxiliar scripts to build the requirements and generate the needed configuration so that project experiments be executed by the Umbra platform.


For instance, to create a configuration specified by a python file that defines an experiment, perform the command below:

```bash
python3 fabric/local-2orgs.py
```

The command will compile the definition of the experiment (and its artifacts) and save it in /tmp/umbra/fabric.
The configuration is saved under a folder of its referenced blockchain project, with the name used to define the experiment, and in a json format. For instance the configuration in the command above will produce a folder /local-2orgs inside the folder /tmp/umbra/fabric/. In the folder /tmp/umbra/fabric/ a file named local-2orgs.json is the one that defines all the configuration of the experiment compile. This file references all the generated topology (nodes and links) and their respective resource profiles and artifacts (e.g., certificates, crypto keys, genesis block).


Similarly, the same takes place with iroha:

```bash
python3 iroha/local-3nodes.py
```

The command will compile the definition of the experiment (and its artifacts) and save it in /tmp/umbra/iroha. A file named local-3nodes.json will be created inside /tmp/umbra/iroha defining the topology and its events, and all the needed material to run the iroha network will be inside the /tmp/umbra/iroha/local-3nodes folder (e.g., the genesis.block, and the configs of each iroha node).


## Running the configurations


1. Start the umbra-cli component:

```bash
umbra-cli --uuid umbra-cli --address 127.0.0.1:9988 --debug --source /tmp/umbra/iroha/ 
```

Specifying --source means all the files in that folder will be available to be loaded by umbra-cli and have experiments performed.

Executing the command above a command line interface (CLI) prompt will start, to exit it just type <ctrl+d>. 
Using the umbra-cli all the interactions with an umbra experiment and its environments is possible. 
The uuid and address fields are needed because umbra-cli uses those parameters to receive status logs from umbra-broker.

2. In umbra-cli, load your configuration:

```bash
umbra-cli> load /tmp/umbra/iroha/local-3nodes.json
```

Loading the configuration means umbra-cli is ready to work with it, meaning the installation of umbra in the defined configuration environments, the start of the umbra components needed in each environment, and the instantiation of the topology and its events as programmed by the experiment. Likewise the tear-down of the topology, stop of the components and uninstall of umbra in the environments is possible to be executed with umbra-cli.


3. In umbra-cli, install the environments of your configuration:

```bash
umbra-cli> install
```

The install command means umbra is going to reach all the environments defined by the configuration, included umbra-default, and install umbra and the dependencies needed to run the experiment in the assigned environments by the configuration. For instance, if a experiment requires fabric/iroha dependencies, all the fabric/iroha container images are going to be downloaded in the environment(s) needed to run the configuration.

4. In umbra-cli, start the components of your configuration:

```bash
umbra-cli> start
```

When start is called, all the components in all the environments are initiated. Each one of those components is a process (e.g., umbra-monitor, umbra-scenario, umbra-broker) with an uuid and address. 

5. In umbra-cli, begin the experiment:

```bash
umbra-cli> begin
```

The begining of an experiment means the instantiation of the topology and the triggering of its events. 


In umbra there is a monitoring component for each environment, triggering the automated monitoring of containers and their hosts to influxdb and ploting those metrics in graphana. 
Then it is possible to access graphana in the address localhost:3000 (username and password: umbra-graphana).


6. In umbra-cli, after performed the instantiation of the topology and the events, it is possible to end the experiment. The command below will require from umbra-broker to tear-down the instantiated topology and stop the monitoring of its components (environments and containers).

```bash
umbra-cli> end
```

7. In umbra-cli, stop the components of your configuration:

```bash
umbra-cli> stop
```

Stop means all the components will be finished in their execution environment.

8. In umbra-cli, if needed, uninstall umbra in the environments of your configuration:

```bash
umbra-cli> uninstall
```

All the uninstall needed to remove umbra and its dependencies will be performed in the configuration environment(s).

9. Type ctrl+d to exit umbra-cli:

```bash
umbra-cli>  <ctrl+d>
```

As nothing happened, umbra-cli is finished.