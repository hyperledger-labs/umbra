Getting Started
===============

1. Install the Main Modules
***************************

$ git clone https://github.com/hyperledger-labs/umbra/

$ cd umbra/build

$ sudo chmod +x build.sh

$ sudo ./build.sh

$ cd -


2. Install the Fabric Requirements
**********************************

$ cd umbra/build

$ sudo chmod +x build_fabric.sh

$ sudo ./build_fabric.sh

$ cd -


3. Create the Fabric Configs
****************************

$ cd umbra/examples/fabric

$ /usr/bin/python3 build_configs.py 

$ cd -


4. Run the Test
***************

$ cd umbra/examples/

$ sudo -H ./run.sh start -c ./fabric/fabric_configs/config_fabric_simple.json 


4. Check the Test Logs
**********************

Notice the different tabs shown by byobu (use ALT + arrows to move among them).

$ sudo -H byobu attach-session -t umbra


4. Stop the Test
****************

$ sudo -H ./run.sh stop