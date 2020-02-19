#!/bin/bash

############ INSTALL ############
# wget https://github.com/protocolbuffers/protobuf/releases/download/v3.11.2/protoc-3.11.2-linux-x86_64.zip
# mkdir protoc
# mv protoc-3.11.2-linux-x86_64.zip ./protoc
# cd protoc
# unzip protoc-3.11.2-linux-x86_64.zip
# sudo cp ./bin/protoc /usr/local/bin/
# sudo cp -R ./include/* /usr/local/include/

# OR INSTALL
# apt install -y protobuf-compiler

# DO NOT USE RELATIVE PATHS
python3 -m grpc_tools.protoc --proto_path=$(pwd) --python_out=$(pwd) --grpc_python_out=$(pwd) umbra.proto

# protoc  --proto_path=/home/raphael/git/github/umbra/umbra/common/protobuf/ --python_out=. --python_grpc_out=. /home/raphael/git/github/umbra/umbra/common/protobuf/umbra.proto

