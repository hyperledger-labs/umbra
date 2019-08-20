from setuptools import setup, find_packages

setup(name='umbra-cfgs',
      version='0.1',
      description='Umbra - Configuration System',
      author='Raphael Vicente Rosa',
      packages=find_packages(),
      include_package_data=True,
      install_requires = [
        'networkx',
        'PyYAML',
        'colorlog',
      ],
)