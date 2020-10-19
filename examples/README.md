# Umbra Examples

This directory contains the useful material to reproduce Hyperledger projects on top of Mininet.

In each folder, referencing a project name, there are auxiliar scripts to build the requirements and generate the needed configuration for that project be executed by the Umbra platform.

## Creating the configuration

To create a configuration specified by a python file that defines an experiment, perform the command below:


```bash
python3 fabric/local-2orgs.py
```

The command will compile the definition of the experiment (and its artifacts) and save it in /tmp/umbra/.


## Running the configuration


1. Start the umbra-cli component:

```bash
umbra-cli --uuid umbra-cli --address 127.0.0.1:9988
```

2. In umbra-cli, load your configuration:

```bash
umbra-cli> load /tmp/umbra/fabric/"configuration-file"
```

3. In umbra-cli, install the environments of your configuration:

```bash
umbra-cli> install
```

4. In umbra-cli, start the components of your configuration:

```bash
umbra-cli> start
```


5. In umbra-cli, begin the experiment:

```bash
umbra-cli> begin
```


6. In umbra-cli, end the experiment:

```bash
umbra-cli> start
```



7. In umbra-cli, stop the components of your configuration:

```bash
umbra-cli> stop
```


8. In umbra-cli, uninstall umbra in the environments of your configuration:

```bash
umbra-cli> uninstall
```


9. Type ctrl+d to exit umbra-cli:

```bash
umbra-cli>  <ctrl+d>
```

