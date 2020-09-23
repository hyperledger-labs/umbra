import logging
import asyncio
import signal

from grpclib.utils import graceful_exit
from grpclib.server import Server

from umbra.common.logs import Logs
from umbra.common.cfg import Config

logger = logging.getLogger(__name__)


logging.getLogger("hpack").setLevel(logging.WARNING)


class App:
    def __init__(self):
        self.cfg = Config()

    def logs(self, screen=True):
        prefix = self.__class__.__name__
        info = self.cfg.get()
        filename = (
            "/tmp/umbra/logs/" + prefix.lower() + "-" + str(info.get("uuid")) + ".log"
        )
        Logs(filename, debug=info.get("debug"), screen=screen)

    async def main(self, app_cls, app_args):
        address = app_args.get("address")
        server = Server([app_cls(app_args)])

        host, port = address.split(":")
        logger.debug(f"Starting server on host {host} : port {port}")

        with graceful_exit([server]):
            await server.start(host, port)
            await server.wait_closed()

    def init(self, app_cls):
        self.logs()
        app_args = self.cfg.get()

        try:
            asyncio.run(self.main(app_cls, app_args))
        except Exception as excpt:
            logger.info(f"Could not init app - exception: {repr(excpt)}")

        finally:
            logger.info("App shutdown complete")
