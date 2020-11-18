#!/bin/bash 

COMMAND=$1

IROHA_TAG="latest"
PS_IROHA_TAG="9.5"


function printHelp() {
    echo_bold "Usage: "
    echo "run.sh <mode> "
    echo "    <mode> - one of 'install' or 'uninstall'"
    echo "      - 'install' - install umbra dependencies - i.e., containernet (and dependencies) for umbra-scenario"
    echo "      - 'uninstall' - uninstall umbra dependencies - i.e., containernet dependencies for umbra-scenario"
    echo "  deps.sh -h (print this message)"

}

export ARCH=$(echo "$(uname -s|tr '[:upper:]' '[:lower:]'|sed 's/mingw64_nt.*/windows/')-$(uname -m | sed 's/x86_64/amd64/g')")
export MARCH=$(uname -m)


installRequirementsIroha() {

  echo "========================================================="
  echo "Installind Iroha Python SDK"
  echo "========================================================="

  sudo apt install -y python3-dev libssl-dev

  mkdir git
  git clone https://github.com/hyperledger/iroha-python git/iroha-python
  cd git/iroha-python
  sudo python3 -m pip install .
  # sudo python3.8 setup.py install
  cd - 
}

dockerIrohaPull() {
    local TAG=$1 
    local PSTAG=$2

    which docker >& /dev/null
    NODOCKER=$?
    if [ "${NODOCKER}" == 0 ]; then       
        docker pull hyperledger/iroha:$TAG
        docker pull postgres:$PSTAG
    else
        echo "========================================================="
        echo "Docker not installed, bypassing download of Iroha images"
        echo "========================================================="
    fi
}

upgradeDockerImages() {
  local TAG=$1
  local PSTAG=$2
  which docker >& /dev/null
  NODOCKER=$?
  if [ "${NODOCKER}" == 0 ]; then
    
    echo "========================================================="
    echo "==> Upgrading IROHA IMAGE "
    echo "========================================================="
    echo
    docker run -ti --name iroha-test hyperledger/iroha:$TAG bash -c 'apt update && apt install -y net-tools iproute2 inetutils-ping && apt clean'
    docker commit iroha-test hyperledger/iroha:$TAG
    echo "-- Committed docker image: hyperledger/iroha:$TAG --"
    docker stop -t0 iroha-test
    docker rm iroha-test
    
    docker run -ti --name iroha-postgres-test postgres:$PSTAG bash -c 'apt update && apt install -y net-tools iproute2 inetutils-ping && apt clean'
    docker commit iroha-postgres-test postgres:$PSTAG
    echo "-- Committed docker image: postgres:$PSTAG --"
    docker stop -t0 iroha-postgres-test
    docker rm iroha-postgres-test
  else
    echo "========================================================="
    echo "Docker not installed, bypassing Upgrade of Iroha images"
    echo "========================================================="
  fi
}



function removeDockerImages() {
    local TAG=$1
    local PSTAG=$2
    echo "========================================================="
    echo "Removing Iroha Docker Images"
    echo "========================================================="

    docker rmi hyperledger/iroha:$TAG
    docker rmi postgres:$PSTAG

}

function uninstall() {

  echo "###################################"
  echo "Uninstalling Iroha Dependencies"
  echo "###################################"

  removeDockerImages ${IROHA_TAG} ${PS_IROHA_TAG}

  echo "========================================================="
  echo "Uninstalling Iroha Python SDK"
  echo "========================================================="

  # sudo apt remove python3-dev libssl-dev

  cd git/iroha-python
  sudo python3 -m pip uninstall -y .
  cd - 
  sudo rm -R git/iroha-python

}

function install() {

  echo "###################################"
  echo "Installing Iroha Dependencies"
  echo "###################################"

  installRequirementsIroha
  dockerIrohaPull ${IROHA_TAG} ${PS_IROHA_TAG}
  upgradeDockerImages ${IROHA_TAG} ${PS_IROHA_TAG}
  
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