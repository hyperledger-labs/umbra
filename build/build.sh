#!/bin/bash 

if [ "$EUID" != "0" ]; then
    echo "Sorry dude! You must be root to run this script."
    exit 1
fi

echo "###################################"
echo "Installing Requirements (Python 3.7)"
echo "###################################"

sudo apt update &&
    apt install -y software-properties-common &&
    add-apt-repository -y ppa:deadsnakes/ppa &&
    apt install python3.7 python3.7-dev python3-pip ansible git aptitude &&

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
