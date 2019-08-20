from setuptools import setup, find_packages

print(find_packages())

setup(name='umbra-scenarios',
      version='0.1',
      description='umbra - Scenarios System',
      author='Raphael Vicente Rosa',
      packages=find_packages(),
      include_package_data=True,
      install_requires = [
        'gevent',
        'requests',
        'Flask',
        'Flask-RESTful',
        'psutil',
        'PyYAML',
      ],
)