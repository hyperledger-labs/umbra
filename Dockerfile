FROM ubuntu:20.04

RUN apt update && apt install -y python3.8 python3-setuptools python3-pip make

RUN python3.8 -m pip install \
        "asyncio>=3.4.3" \
        "protobuf>=3.11.0" \
        "grpclib>=0.3.1" \
        "grpcio-tools>=1.26.0" \
        "PyYAML>=5.1.2" \
        "networkx>=2.4" \
        "psutil>=5.6.7" \
        "docker<=4.1.0" \
        "prompt_toolkit<=3.0.6" \
        "paramiko<=2.6.0" \
        "scp<=0.13.2"

RUN mkdir -p /umbra

COPY ./deps /umbra/deps
COPY ./examples /umbra/examples
COPY ./umbra /umbra/umbra
COPY ./setup.py /umbra/
COPY ./Makefile /umbra/
COPY ./README.md /umbra/

WORKDIR /umbra

RUN make install

CMD [ "umbra-cli" ]