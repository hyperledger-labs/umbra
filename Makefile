.PHONY: clean-pyc clean-build
.DEFAULT_GOAL := help

TEST_PATH=./umbra/tests

DEPS_FOLDER=./deps
DEPS=deps.sh
DEPS_FABRIC=deps_fabric.sh
DEPS_IROHA=deps_iroha.sh

AUX_FOLDER=./aux
AUX_MONITOR=monitor.sh


install-fabric:
	sh -c "cd $(DEPS_FOLDER) && ./$(DEPS_FABRIC) install && cd - "

uninstall-fabric:
	sh -c "cd $(DEPS_FOLDER) && ./$(DEPS_FABRIC) uninstall && cd - "

install-iroha:
	sh -c "cd $(DEPS_FOLDER) && ./$(DEPS_IROHA) install && cd - "

uninstall-iroha:
	sh -c "cd $(DEPS_FOLDER) && ./$(DEPS_IROHA) uninstall && cd - "

vagrant-requirements-virtualbox:
	sudo apt install -y vagrant

	sudo apt install -y virtualbox
	sudo apt-get install -y linux-headers-generic
	sudo dpkg-reconfigure virtualbox-dkms
	sudo dpkg-reconfigure virtualbox
	sudo modprobe vboxdrv
	sudo modprobe vboxnetflt

vagrant-requirements-libvirt:
	sudo apt install -y vagrant
	sudo apt-get install -y qemu-kvm qemu-utils libvirt-daemon bridge-utils virt-manager libguestfs-tools virtinst rsync
	sudo apt-get install -y ruby-libvirt libvirt-dev
	vagrant plugin install vagrant-libvirt

requirements:
	sudo apt update && sudo apt install -y git python3.8 python3-setuptools python3-pip
	mkdir -p /tmp/umbra
	mkdir -p /tmp/umbra/logs
	mkdir -p /tmp/umbra/source

install-deps:
	sh -c "cd $(DEPS_FOLDER) && ./$(DEPS) install && cd - "

uninstall-deps:
	sh -c "cd $(DEPS_FOLDER) && ./$(DEPS) uninstall && cd - "
    
install: requirements install-deps
	sudo /usr/bin/python3.8 setup.py develop
	# sudo /usr/bin/python3.8 -m pip install .

develop: requirements
	sudo /usr/bin/python3.8 setup.py develop

uninstall:
	sudo /usr/bin/python3.8 -m pip uninstall -y umbra
    
clean-pyc:
	sudo sh -c "find . -name '*.pyc' -exec rm --force {} + "
	sudo sh -c "find . -name '*.pyo' -exec rm --force {} + "
	sudo sh -c "find . -name '*~' -exec rm --force  {} + "

clean-build:
	sudo sh -c "rm --force --recursive build/"
	sudo sh -c "rm --force --recursive dist/"
	sudo sh -c "rm --force --recursive *.egg-info"

clean: clean-build clean-pyc
	sudo rm -R /tmp/umbra
	
isort:
	sh -c "isort --skip-glob=.tox --recursive . "

lint:
	flake8 --exclude=.tox

test: clean-pyc
	py.test --verbose --color=yes $(TEST_PATH)

run: install
	umbra-cli --help

docker-build:
	docker build \
	--tag=umbra:latest .

docker-run: docker-build
	docker run \
	--detach=false \
	--name=umbra \
	umbra:latest umbra-cli

vagrant-run-virtualbox: requirements-vagrant-virtualbox
	vagrant up --provider virtualbox

vagrant-run-libvirt: vagrant-requirements-libvirt
	vagrant up --provider libvirt

start-aux-monitor:
	sh -c "cd $(AUX_FOLDER) && ./$(AUX_MONITOR) start && cd - "

stop-aux-monitor:
	sh -c "cd $(AUX_FOLDER) && ./$(AUX_MONITOR) stop && cd - "

all: requirements install run



help:
	@echo ""
	@echo "     				umbra makefile help"
	@echo "           ---------------------------------------------------------"
	@echo ""
	@echo "     requirements"
	@echo "         Install umbra requirements (i.e., python3.8 python3-setuptools python3-pip)."
	@echo "     vagrant-requirements-virtualbox"
	@echo "         Install the requirements to build a virtual machine with umbra installed using virtualbox."
	@echo "     vagrant-requirements-libvirt"
	@echo "         Install the requirements to build a virtual machine with umbra installed using qemu-kvm."
	@echo "     install-fabric"
	@echo "         Install fabric dependencies (images, python SDK, golang)."
	@echo "     uninstall-fabric"
	@echo "         Remove fabric dependencies (images, python SDK, ...)."
	@echo "     install-iroha"
	@echo "         Install iroha dependencies (images, python SDK)."
	@echo "     uninstall-iroha"
	@echo "         Remove iroha dependencies (images, python SDK, ...)."
	@echo "     install-deps"
	@echo "         Install umbra-scenario dependencies (i.e., containernet)."
	@echo "     uninstall-deps"
	@echo "         Uninstall umbra-scenario dependencies (i.e., containernet)."
	@echo "     develop"
	@echo "         Run python3.8 setup.py develop."
	@echo "     install"
	@echo "         Setup with pip install . ."
	@echo "     uninstall"
	@echo "         Remove umbra with pip uninstall umbra."
	@echo "     clean-pyc"
	@echo "         Remove python artifacts."
	@echo "     clean-build"
	@echo "         Remove build artifacts."
	@echo "     clean"
	@echo "         Remove build and python artifacts (clean-build clean-pyc)."
	@echo "     isort"
	@echo "         Sort import statements."
	@echo "     lint"
	@echo "         Check style with flake8."
	@echo "     test"
	@echo "         Run py.test in umbra/tests folder"
	@echo "     run"
	@echo "         Run the umbra-cli on your local machine."
	@echo "     docker-run"
	@echo "         Build and run the umbra-cli in a Docker container."
	@echo "     vagrant-run-virtualbox"
	@echo "         Build and run a virtual machine with umbra installed using virtualbox."
	@echo "     vagrant-run-libvirt"
	@echo "         Build and run a virtual machine with umbra installed using qemu-kvm."
	@echo "     start-aux-monitor"
	@echo "         Create and start the aux containers for monitoring (influxdb and graphana)."
	@echo "     stop-aux-monitor"
	@echo "         Stop and remove the aux containers for monitoring (influxdb and graphana)."
	@echo ""
	@echo "           ---------------------------------------------------------"
	@echo ""