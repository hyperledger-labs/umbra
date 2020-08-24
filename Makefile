.PHONY: clean-pyc clean-build
.DEFAULT_GOAL := help
TEST_PATH=./umbra/tests
DEPS_FOLDER=./deps
DEPS=deps.sh
DEPS_FABRIC=deps_fabric.sh

install-fabric:
	sh -c "cd $(DEPS_FOLDER) && ./$(DEPS_FABRIC) install && cd - "

uninstall-fabric:
	sh -c "cd $(DEPS_FOLDER) && ./$(DEPS_FABRIC) uninstall && cd - "

requirements:
	apt update && apt install -y python3.8 python3-setuptools python3-pip

install-deps:
	sh -c "cd $(DEPS_FOLDER) && ./$(DEPS) install && cd - "

uninstall-deps:
	sh -c "cd $(DEPS_FOLDER) && ./$(DEPS) uninstall && cd - "
    
install: requirements
	/usr/bin/python3.8 setup.py develop
	# /usr/bin/python3.8 -m pip install .

uninstall:
	/usr/bin/python3.8 -m pip uninstall -y umbra
    
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

run: install
	umbra-cli

docker-build:
	docker build \
	--tag=umbra:latest .

docker-run: docker-build
	docker run \
	--detach=false \
	--name=umbra \
	umbra:latest umbra-cli

all: requirements install run



help:
	@echo ""
	@echo "     				umbra makefile help"
	@echo "           ---------------------------------------------------------"
	@echo ""
	@echo "     requirements"
	@echo "         Install umbra requirements (i.e., python3.8 python3-setuptools python3-pip)."
	@echo "     install-fabric"
	@echo "         Install fabric dependencies (images, python SDK, golang)."
	@echo "     uninstall-fabric"
	@echo "         Remove fabric dependencies (images, python SDK, ...)."
	@echo "     install-deps"
	@echo "         Install umbra-scenario dependencies (i.e., containernet)."
	@echo "     uninstall-deps"
	@echo "         Uninstall umbra-scenario dependencies (i.e., containernet)."
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
	@echo ""
	@echo "           ---------------------------------------------------------"
	@echo ""