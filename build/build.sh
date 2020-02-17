#!/bin/bash 

echo "###################################"
echo "Installing Requirements"
echo "###################################"

sudo apt update && apt install python3-dev python3-pip ansible git aptitude
sudo pip3 install setuptools

echo "###################################"
echo "Installing Umbra"
echo "###################################"

cd ../
sudo python3 setup.py develop
cd -

echo "###################################"
echo "Installing Containernet"
echo "###################################"

git clone https://github.com/raphaelvrosa/containernet
cd containernet/ansible
sudo ansible-playbook -i "localhost," -c local install.yml
cd ..
sudo python3 setup.py install
cd ..
