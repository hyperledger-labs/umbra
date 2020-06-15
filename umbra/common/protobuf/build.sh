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

# DO NOT USE RELATIVE PATHS: Run this line inside the folder umbra/umbra/common/protobuf
# python3 -m grpc_tools.protoc --proto_path=$(pwd) --python_out=$(pwd) --grpc_python_out=$(pwd) umbra.proto
python3 -m grpc_tools.protoc -I. --python_out=. --grpclib_python_out=. umbra.proto


