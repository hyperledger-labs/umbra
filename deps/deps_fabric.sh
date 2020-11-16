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

# export VERSION=2.2
# if ca version not passed in, default to latest released version
# export CA_VERSION=1.4.7
export ARCH=$(echo "$(uname -s|tr '[:upper:]' '[:lower:]'|sed 's/mingw64_nt.*/windows/')-$(uname -m | sed 's/x86_64/amd64/g')")
export MARCH=$(uname -m)


CA_TAG="1.4.7"
FABRIC_TAG="2.2"

installRequirementsFabric() {

  echo "========================================================="
  echo "Installind Go"
  echo "========================================================="

  sudo apt install -y golang-go

  mkdir $HOME/go
  mkdir $HOME/go/bin
  mkdir $HOME/go/src
  mkdir $HOME/go/pkg

  sudo echo 'export GOPATH=$HOME/go' >> ~/.profile
  sudo echo 'export GOBIN=$HOME/go/bin' >> ~/.profile
  sudo echo 'export PATH=$PATH:/usr/local/go/bin:$GOBIN' >> ~/.profile

  source ~/.profile

  echo "========================================================="
  echo "Installind Fabric Python SDK"
  echo "========================================================="

  sudo apt install -y python3-dev libssl-dev

  mkdir git
  git clone https://github.com/hyperledger/fabric-sdk-py git/fabric-sdk-py
  cd git/fabric-sdk-py
  sudo python3.8 -m pip install .
  # sudo python3.8 setup.py install
  cd - 
}

dockerFabricPull() {
  local FABRIC_TAG=$1
#   for IMAGES in peer orderer ccenv tools; do
  for IMAGES in peer orderer; do
      echo "==> FABRIC IMAGE: $IMAGES"
      echo
      docker pull hyperledger/fabric-$IMAGES:$FABRIC_TAG
      docker tag hyperledger/fabric-$IMAGES:$FABRIC_TAG hyperledger/fabric-$IMAGES
  done
}

dockerThirdPartyImagesPull() {
  local THIRDPARTY_TAG=$1
  for IMAGES in couchdb kafka zookeeper; do
      echo "==> THIRDPARTY DOCKER IMAGE: $IMAGES"
      echo
      docker pull hyperledger/fabric-$IMAGES:$THIRDPARTY_TAG
      docker tag hyperledger/fabric-$IMAGES:$THIRDPARTY_TAG hyperledger/fabric-$IMAGES
  done
}

dockerCaPull() {
      local CA_TAG=$1
      echo "==> FABRIC CA IMAGE"
      echo
      docker pull hyperledger/fabric-ca:$CA_TAG
      docker tag hyperledger/fabric-ca:$CA_TAG hyperledger/fabric-ca
}

createDockerImages() {
  which docker >& /dev/null
  NODOCKER=$?
  if [ "${NODOCKER}" == 0 ]; then
	  echo "========================================================="
      echo "===> Pulling fabric Images"
      echo "========================================================="
	  dockerFabricPull ${FABRIC_TAG}
	  echo "===> Pulling fabric ca Image"
	  dockerCaPull ${CA_TAG}
	#   echo "===> Pulling thirdparty docker images"
	#   dockerThirdPartyImagesPull ${THIRDPARTY_TAG}
	  echo
	  echo "===> List out hyperledger docker images"
	  docker images | grep hyperledger*
  else
    echo "========================================================="
    echo "Docker not installed, bypassing download of Fabric images"
    echo "========================================================="
  fi
}


upgradeDockerImages() {
  local TAG=$1
  which docker >& /dev/null
  NODOCKER=$?
  if [ "${NODOCKER}" == 0 ]; then
    for IMAGES in peer; do
        echo "========================================================="
        echo "==> Upgrading FABRIC IMAGE: $IMAGES:$TAG"
        echo "========================================================="
        echo
        docker run -ti --name $IMAGES hyperledger/fabric-$IMAGES:$TAG /bin/sh -c 'apk add --no-cache iputils bash'
        # docker exec $IMAGES bash -c 'apt update && apt install -y net-tools iproute2 inetutils-ping && apt clean'  
        # docker exec fabric-orderer /bin/sh -c 'apk update && apk add iputils bash'
        docker commit $IMAGES hyperledger/fabric-$IMAGES:$TAG.1
        echo "-- Committed docker image: hyperledger/fabric-$IMAGES:$TAG.1 --"
        # docker stop -t0 $IMAGES
        docker rm $IMAGES 
      done

    echo "========================================================="
    echo "==> Upgrading FABRIC IMAGE: fabric-orderer:$TAG"
    echo "========================================================="
    echo
    docker run -ti --name fabric-orderer hyperledger/fabric-orderer:$TAG /bin/sh -c 'apk add --no-cache iputils bash'
    # docker exec fabric-orderer bash -c 'apt update && apt install -y net-tools iproute2 inetutils-ping && apt clean && rm -R /var/hyperledger/*'
    # docker exec fabric-orderer /bin/sh -c 'apk update && apk add iputils bash'
    docker commit fabric-orderer hyperledger/fabric-orderer:$TAG.1
    echo "-- Committed docker image: hyperledger/fabric-orderer:$TAG.1 --"
    # docker stop -t0 fabric-orderer
    docker rm fabric-orderer


    echo "========================================================="
    echo "==> Upgrading FABRIC IMAGE: fabric-ca:$CA_TAG"
    echo "========================================================="
    echo
    docker run -d --name fabric-ca hyperledger/fabric-ca:$CA_TAG
    docker exec fabric-ca bash -c 'apt update && apt install -y net-tools iproute2 inetutils-ping && apt clean'
    docker commit fabric-ca hyperledger/fabric-ca:$CA_TAG.1
    echo "-- Committed docker image: hyperledger/fabric-ca:$CA_TAG.1 --"
    docker stop -t0 fabric-ca
    docker rm fabric-ca

  else
    echo "========================================================="
    echo "Docker not installed, bypassing Upgrade of Fabric images"
    echo "========================================================="
  fi
}



function removeDockerImages() {

  echo "========================================================="
  echo "Removing Fabric Docker Images"
  echo "========================================================="

  docker rmi \
    hyperledger/fabric-ca:$CA_TAG.1 \
    hyperledger/fabric-orderer:$FABRIC_TAG.1 \
    hyperledger/fabric-peer:$FABRIC_TAG.1 \
    hyperledger/fabric-ca:$CA_TAG \
    hyperledger/fabric-orderer:$FABRIC_TAG \
    hyperledger/fabric-peer:$FABRIC_TAG

}

function uninstall() {

  echo "###################################"
  echo "Uninstalling Fabric Dependencies"
  echo "###################################"

  removeDockerImages

  echo "========================================================="
  echo "Uninstalling Fabric Python SDK"
  echo "========================================================="

  # sudo apt remove python3-dev libssl-dev

  cd git/fabric-sdk-py
  sudo python3.8 -m pip uninstall -y .
  cd - 
  sudo rm -R git/fabric-sdk-py

  echo "========================================================="
  echo "Uninstalling Go - Removing Go Dirs (bin, src, pkg)"
  echo "========================================================="

  # sudo apt remove -y golang-go
  # sudo rm -R $HOME/go
  # TODO: use sed to remove lines from ~/.profile
  # sudo sed '/export GOPATH=$HOME/go' >> ~/.profile
  # sudo sed '/export GOBIN=$HOME/go/bin' >> ~/.profile
  # sudo sed '/export PATH=$PATH:/usr/local/go/bin:$GOBIN' >> ~/.profile
  # source ~/.profile

  echo "========================================================="
  echo "Removes configtxgen and cryptogen to PATH env"
  echo "========================================================="
  sudo rm -R $HOME/hl
}

function install() {

  echo "###################################"
  echo "Installing Fabric Dependencies"
  echo "###################################"

  installRequirementsFabric
  createDockerImages
  upgradeDockerImages ${FABRIC_TAG}

  echo "========================================================="
  echo "Adds configtxgen and cryptogen to PATH env"
  echo "========================================================="

  mkdir -p $HOME/hl/bin
  cp ./fabric/* $HOME/hl/bin/
  sudo echo 'export PATH=$PATH:$HOME/hl/bin' >> ~/.profile
  source ~/.profile

   
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