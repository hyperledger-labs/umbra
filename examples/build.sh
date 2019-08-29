#!/bin/bash 

sudo apt update && apt install ansible git aptitude

echo "###################################"
echo "Clonning Containernet"
echo "###################################"

git clone https://github.com/raphaelvrosa/containernet

echo "###################################"
echo "Installing Containernet"
echo "###################################"

cd containernet/ansible
sudo ansible-playbook -i "localhost," -c local install.yml
cd ..
sudo python setup.py install