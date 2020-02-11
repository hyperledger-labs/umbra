#!/bin/bash

python3 -m grpc_tools.protoc --proto_path=$(pwd) --python_out=$(pwd) --grpc_python_out=$(pwd) umbra.proto

# protoc  --proto_path=/home/raphael/git/github/umbra/umbra/common/protobuf/ --python_out=. --python_grpc_out=. /home/raphael/git/github/umbra/umbra/common/protobuf/umbra.proto

