import logging
import argparse
import yaml

logger = logging.getLogger(__name__)


class Config:
    def __init__(self):
        self._info = None

    def get(self):
        return self._info

    def load(self, filename):
        data = {}
        with open(filename, 'r') as f:
            data = yaml.load(f, Loader=yaml.SafeLoader)
        return data

    def parse(self, argv=None):
        parser = argparse.ArgumentParser(
            description='Umbra App')

        parser.add_argument('--uuid',
                            type=str,
                            help='Define the app unique id (default: None)')

        parser.add_argument('--address',
                            type=str,
                            help='Define the app address (host:port) (default: None)')

        parser.add_argument('--debug',
                            action='store_true',
                            help='Define the app logging mode (default: False)')

        self.cfg, _ = parser.parse_known_args(argv)
        
        info = self.check()
        if info:
            self._info = info
            return True
        
        return False

    def cfg_args(self):
        cfgFile = self.cfg.cfg
        if cfgFile:
            cfg_data = self.load(cfgFile)
            return cfg_data
        return None
            
    def check(self):
        _uuid, _address = self.cfg.uuid, self.cfg.address

        if _uuid and _address:
            logger.info("Init cfg: id %s - address %s", _uuid, _address)
            info = {
                "uuid": _uuid,
                "address": _address,
                "debug": self.cfg.debug
            }
            print(f'Argv: {info}')
            return info
        else:
            print("Init cfg NOT provided - both must exist: uuid and address (provided values: %s, %s)" % (_uuid, _address))
            return None
