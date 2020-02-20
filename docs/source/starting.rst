Getting Started
===============

The steps below comprehend how to install and run a Fabric topology using Umbra.

Requirements
************

Umbra works on Ubuntu 18.04.

To run the getting started example it is recommended a machine with Ubuntu 18.04 installed and containing 4 vCPUs (cores), 4 GB of memory, and at least 5GB of disk available.


1. Install the Main Components
******************************

Umbra contains 3 python components (design, broker, scenario), the build script below installs the requirements and the components themselves.


.. code-block:: bash

    $ git clone https://github.com/hyperledger-labs/umbra/

    $ cd umbra/build

    $ sudo chmod +x build.sh

    $ ./build.sh

    $ cd -

Please note, the script above (build.sh) install docker-ce and adds the $USER to the docker group (no need to user sudo before the docker command). To enable this setting, logout and login again, or execute `su $USER` (to start a new session). You can test if it works simply running `docker ps -a`.


2. Install the Fabric Requirements
**********************************

As Umbra is plugin oriented (i.e., each Hyperledger project needs its own umbra-plugin), the build_fabric script below installs all the Fabric (v1.4) components needed to run the Umbra Fabric plugin.

.. code-block:: bash

    $ cd umbra/build

    $ sudo chmod +x build_fabric.sh

    $ ./build_fabric.sh

    $ cd -


3. Create the Fabric Configs
****************************

The build_configs script below creates the config files for the Fabric scenario.
Open this file to see what is the scenario created, the topology and its events.

.. code-block:: bash

    $ cd umbra/examples/fabric

    $ /usr/bin/python3 build_configs.py 

    $ cd -


4. Run the Test
***************

The run.sh script below executes the Fabric scenario (topology and events).
In order to run the Mininet, a sudo password will be asked to run the Umbra scenario component.

.. code-block:: bash

    $ cd umbra/examples/

    $ ./run.sh start -c ./fabric/fabric_configs/config_fabric_simple.json



4. Check the Test Logs
**********************

As the broker and scenario components save logs during their execution, they can be seen by the commands below.

.. code-block:: bash

    $ tail -f logs/broker.log

    $ tail -f logs/scenario.log


4. Stop the Test
****************

The command below stops all the Umbra processes and clean their breadcrumbs. 

.. code-block:: bash

    $ ./run.sh stop