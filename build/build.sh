#!/bin/bash 

echo "###################################"
echo "Installing Requirements (Python 3.7)"
echo "###################################"

sudo apt update &&
    sudo apt install -y software-properties-common &&
    sudo add-apt-repository -y ppa:deadsnakes/ppa &&
    sudo apt install -y python3.7 python3.7-dev python3-dev python3-pip ansible git aptitude

sudo pip3 install setuptools

echo "###################################"
echo "Installing Umbra"
echo "###################################"

cd ../
sudo python3.7 setup.py develop
cd -

echo "###################################"
echo "Installing Containernet"
echo "###################################"

sudo python3.7 -m pip install -U docker-py cffi pexpect

git clone https://github.com/raphaelvrosa/containernet
cd containernet/ansible
sudo ansible-playbook -i "localhost," -c local install.yml
cd ..
sudo python3.7 setup.py install
cd ..

sudo usermod -aG docker $USER