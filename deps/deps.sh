#!/bin/bash 

COMMAND=$1

function printHelp() {
    echo_bold "Usage: "
    echo "run.sh <mode> "
    echo "    <mode> - one of 'install' or 'uninstall'"
    echo "      - 'install' - install umbra dependencies - i.e., containernet (and dependencies) for umbra-scenario"
    echo "      - 'uninstall' - uninstall umbra dependencies - i.e., containernet dependencies for umbra-scenario"
    echo "  deps.sh -h (print this message)"

}


function install() {

    echo "###################################"
    echo "Installing Umbra Dependencies"
    echo "###################################"

    sudo apt update && sudo apt install -y curl wget ansible git aptitude python3-pip
    sudo python3.8 -m pip install -U "docker<=4.1.0" cffi pexpect

    git clone https://github.com/raphaelvrosa/containernet git/containernet
    cd git/containernet/ansible
    sudo ansible-playbook -i "localhost," -c local install.yml
    cd ..
    sudo python3.8 -m pip install .
    cd ..

    # sudo usermod -aG docker $USER

    echo "###################################"
    echo "Downloading Images for Monitoring Umbra: influxdb and graphana"
    echo "###################################"

    docker pull influxdb:latest
    docker pull grafana/grafana:latest

}

function uninstall() {

    echo "###################################"
    echo "Uninstalling Umbra Dependencies"
    echo "###################################"

    cd containernet/ansible
    sudo ansible-playbook -i "localhost," -c local install.yml
    cd ..
    sudo python3.8 -m pip uninstall -y .
    cd ..

    # sudo apt update && sudo apt remove -y curl wget ansible git aptitude
    # sudo python3.8 -m pip uninstall "docker<=4.1.0" cffi pexpect

}


case "$COMMAND" in
    install)
        install
        exit 0
        ;;  

    uninstall)
        uninstall
        exit 0
        ;;
    *)
        printHelp
        exit 1
esac
