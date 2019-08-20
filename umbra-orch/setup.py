from setuptools import setup, find_packages

setup(name='umbra-orch',
      version='0.1',
      description='Umbra - Orchestration System',
      author='Raphael Vicente Rosa',
      packages=find_packages(),
      include_package_data=True,
      install_requires = [
        'asyncio',
        'aiohttp',
        'colorlog',
      ],
)
