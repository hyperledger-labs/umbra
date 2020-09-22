from setuptools import setup, find_packages

with open("README.md") as f:
    readme = f.read()

with open("umbra/__init__.py") as f:
    for line in f:
        if line.startswith("__version__"):
            version = line.split('"')[1]

setup(
    name="umbra",
    version=version,
    description="Umbra - Emulating Hyperledger Blockchains",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="Raphael Vicente Rosa",
    packages=find_packages(exclude=("tests",)),
    namespace_packages=["umbra"],
    include_package_data=True,
    keywords=["umbra", "emulator", "hyperledger", "blockchain"],
    license="Apache License v2.0",
    url="https://github.com/raphaelvrosa/umbra",
    download_url="https://github.com/raphaelvrosa/umbra",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Topic :: Utilities",
        "License :: OSI Approved :: Apache Software License",
    ],
    scripts=[
        "umbra/cli/umbra-cli",
        "umbra/broker/umbra-broker",
        "umbra/scenario/umbra-scenario",
        "umbra/agent/umbra-agent",
        "umbra/monitor/umbra-monitor",
    ],
    install_requires=[
        "asyncio==3.4.3",
        "protobuf==3.12.2",
        "grpclib==0.3.2",
        "grpcio-tools==1.31.0",
        "PyYAML==5.3.1",
        "networkx==2.4",
        "psutil==5.7.0",
        "docker==4.1.0",
        "paramiko==2.6.0",
        "scp==0.13.2",
        "prompt_toolkit==3.0.6",
        "influxdb==5.3.0",
    ],
    python_requires=">=3.8",
    setup_requires=["setuptools>=41.1.0"],
)
