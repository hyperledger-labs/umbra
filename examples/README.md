# Umbra Examples

This directory contains the useful material to reproduce Hyperledger projects on top of Mininet.

In each folder, referencing a project name, there are auxiliar scripts to build the requirements and generate the needed configuration for that project be executed by the Umbra platform.

## Installing

Currently, umbra consist of three modules: umbra-[configs, orch, scenarios].

All these packages, and their requirements, can be installed using the command below.
This command requires root privileges. It installs umbra modules in the host machine.

```bash
cd ../ #Given that the current directory is umbra/examples
$ sudo ./build.sh
cd -
```

Besides of installing all the umbra modules, each Hyperledger project has its own requirements, which must also be fulfilled.
For instance, in the folder umbra/examples/fabric there exists a script build_reqs.sh that downloads and tags all the Fabric docker images needed to execute a Fabric network on Mininet.

Mostly important, in addition to those scripts, a must to run any umbra project concerns the installation of the Mininet platform, in the shape of an enhancement named Containernet, able to execute docker containers.
To perform such task, while in the examples directory, execute the script:

```bash
$ sudo ./build.sh
```

Given that, now you are able to run the examples contained in this folder. In each folder you have a README.md file explaining how to proceed with its execution by umbra. 

In summary, the run.sh script contained in this folder (umbra/examples) runs all the configuration files created in each project folder.
Take a look at the umbra/examples/fabric/README.md as an initial step.  




