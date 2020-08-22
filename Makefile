.DEFAULT_GOAL := all

TEST_PATH=./umbra/tests

DEPS_FOLDER=./deps
DEPS=deps.sh
DEPS_FABRIC=deps_fabric.sh


requirements:
	apt update && apt install -y python3.8 python3-setuptools python3-pip

install-fabric:
	sh -c "cd $(DEPS_FOLDER) && ./$(DEPS_FABRIC) install && cd - "

uninstall-fabric:
	sh -c "cd $(DEPS_FOLDER) && ./$(DEPS_FABRIC) uninstall && cd - "
	
install-deps:
	sh -c "cd $(DEPS_FOLDER) && ./$(DEPS) install && cd - "

uninstall-deps:
	sh -c "cd $(DEPS_FOLDER) && ./$(DEPS) uninstall && cd - "

install: requirements
	/usr/bin/python3.8 setup.py develop
	/usr/bin/python3.8 -m pip install .

uninstall:
	/usr/bin/python3.8 -m pip uninstall umbra

clean-pyc:
	sudo sh -c "find . -name '*.pyc' -exec rm --force {} + "
	sudo sh -c "find . -name '*.pyo' -exec rm --force {} + "
	sudo sh -c "find . -name '*~' -exec rm --force  {} + "

clean-build:
	sudo sh -c "rm --force --recursive build/"
	sudo sh -c "rm --force --recursive dist/"
	sudo sh -c "rm --force --recursive *.egg-info"

clean: clean-build clean-pyc

isort:
	sh -c "isort --skip-glob=.tox --recursive . "

lint:
	flake8 --exclude=.tox

test: clean-pyc
	py.test --verbose --color=yes $(TEST_PATH)

run:
	umbra-cli

docker-build:
	docker build \
	--tag=umbra:latest .

docker-run:
	docker run \
	--detach=false \
	--name=umbra \
	umbra:latest umbra-cli

all: requirements install run