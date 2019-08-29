import sys
import json
import asyncio
from aiohttp import web

from umbra_orch.app import App
from umbra_orch.manager import Manager

import logging
import logging.config

logger = logging.getLogger(__name__)


class Logs:
    def __init__(self, filename, debug=False):

        op_mode = "DEBUG" if debug else "INFO"

        logging.config.dictConfig({
                'version': 1,
                'disable_existing_loggers': False,
                'formatters': {
                    'standard': {
                        'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
                    },
                },
                'handlers': {
                    'default': {
                        'level':op_mode,
                        'class':'logging.StreamHandler',
                        "formatter": "standard",
                    },
                    "info_file_handler": {
                        "class": "logging.handlers.RotatingFileHandler",
                        "level": "DEBUG",
                        "formatter": "standard",
                        "filename": filename,
                        "maxBytes": 10485760,
                        "backupCount": 20,
                        "encoding": "utf8"
                    },
                },
                'loggers': {
                    '': {
                        'handlers': ['default', 'info_file_handler'],
                        'level': 'DEBUG',
                        'propagate': True
                    }
                }
            })


class Orch(App):
    def __init__(self):
        App.__init__(self)
        self.manager = None
        self._ids = 0

    def validate_payload(self, raw_data):
        payload = raw_data.decode(encoding='UTF-8')
        try:
            parsed = json.loads(payload)
        except ValueError:
            raise Exception('Payload is not json serialisable')
        return parsed

    async def handle(self, request):
        raw_data = await request.read()
        data = self.validate_payload(raw_data)
        request.loop.create_task(self.manage(data))
        # self.loop.create_task(self.manage(data))
        return web.HTTPOk(text="ack")
        
    async def manage(self, data):        
        await asyncio.sleep(0.01) # Makes webHTTPOk return immediately
        logging.debug("Handled Ok -> Manager Workflow")
        outputs = self.manager.workflow(data)
        await self.exit(outputs)

    async def exit(self, outputs):
        if outputs:
            for output in outputs:
                url = output["to"]
                data = output["data"]
                if url:
                    logger.info("url %s - data %s", url, data)
                    exit_reply = await self.send(url, data)
                    logger.info("exit_reply %s", exit_reply)
                else:
                    logger.info("No callback provided for %s", output)
        else:
            logger.info("nothing to output")

    def logs(self, conf):
        filename = "/tmp/cl-orch.log"
        Logs(filename, debug=conf.debug)

    def run(self, argv):
        self.conf = self.get_config(argv)
        self.logs(self.conf)
        self.manager = Manager(self.loop, self.conf, self.exit)
        self.main()


def main():
    app = Orch()
    app.run(sys.argv[1:])
