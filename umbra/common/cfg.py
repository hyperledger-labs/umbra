import logging
import argparse
import yaml

logger = logging.getLogger(__name__)


class Config:
    def __init__(self):
        self._info = None
        self.cfg = {}
        self.parser = argparse.ArgumentParser(description="Umbra App")

    def get(self):
        return self._info

    def get_cfg_attrib(self, name):
        try:
            value = getattr(self.cfg, name)
        except AttributeError as e:
            logger.debug(f"Argparser attrib name not found - exception {e}")
            value = None
        finally:
            return value

    def load(self, filename):
        data = {}
        with open(filename, "r") as f:
            data = yaml.load(f, Loader=yaml.SafeLoader)
        return data

    def parse(self, argv=None):
        self.parser.add_argument(
            "--uuid", type=str, help="Define the app unique id (default: None)"
        )

        self.parser.add_argument(
            "--address",
            type=str,
            help="Define the app address (host:port) (default: None)",
        )

        self.parser.add_argument(
            "--debug",
            action="store_true",
            help="Define the app logging mode (default: False)",
        )

        self.cfg, _ = self.parser.parse_known_args(argv)

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

    def check_address_fmt(self, address):
        ack = True

        try:
            ip, port = address.split(":")
        except ValueError as e:
            print(f"Address must contain ip:port format")
            print(f"Exception checking address format {e}")
            ack = False
        else:
            if not ip or not port:
                print(f"Address must contain ip and port")
                ack = False

        finally:
            return ack

    def check(self):
        _uuid, _address = self.cfg.uuid, self.cfg.address

        if self.cfg.uuid and self.cfg.address:

            address_ok = self.check_address_fmt(self.cfg.address)

            if address_ok:

                info = {
                    "uuid": self.cfg.uuid,
                    "address": self.cfg.address,
                    "debug": self.cfg.debug,
                }
                # print(
                #     f"App cfg args OK: uuid {self.cfg.uuid} - address {self.cfg.address} - debug {self.cfg.debug}"
                # )
                return info
            else:
                print(
                    f"App cfg args not OK: address {self.cfg.address} in wrong format"
                )
                return None

        else:
            print(
                "Init cfg NOT provided - both must exist: uuid and address (provided values: %s, %s)"
                % (_uuid, _address)
            )
            return None
