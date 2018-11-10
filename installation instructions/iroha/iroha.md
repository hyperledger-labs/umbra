## Hyperledger Iroha and Shadow

The instructions assumes that you have Debian 9 or Ubuntu 18.10 OS installed in your
system. If you do not have such OS you can setup using Qemu or a VM.

- Install `asciinema`.
- Run `asciinema play iroha-build-asciinema.json`
- Install [Shadow](https://github.com/shadow/shadow). The detailed instructions are
available [here](https://github.com/shadow/shadow/wiki/1.1-Shadow). You can find the
Docker instructions [here](https://github.com/shadow/shadow/wiki/1.2-Shadow-with-Docker).
- To setup the test network and run Shadow use [shadow.config.xml](./shadow.config.xml)
configuration file, see [this](https://github.com/shadow/shadow/wiki/3.1-Shadow-Config) for more info.


For Ubuntu 18.10 install the below packages before following above installation
instructions:

- Install `libc-ares-dev`.
- Install protobuf using the following instructions
     - `curl -OL https://github.com/google/protobuf/releases/download/v3.5.1/protoc-3.5.1-linux-x86_64.zip`
     - `unzip protoc-3.5.1-linux-x86_64.zip -d protoc`
     - `sudo mv protoc/bin/* /usr/local/bin/`
     - `sudo mv protoc/include/* /usr/local/include/`
     - `sudo chown $USER /usr/local/bin/protoc`
     - `sudo chown -R $USER /usr/local/include/google`
