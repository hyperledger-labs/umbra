import sys
import argparse
import logging
import asyncio
import aiohttp
from aiohttp import web


logger = logging.getLogger(__name__)

class App():
    def __init__(self):
        self.conf = None
        self.handler = None
        self.loop = asyncio.get_event_loop()

    async def handle(self, request):
        pass

    def setup_routes(self, app, handler):
        router = app.router
        # router.add_get('/', handler.index, name='index')
        router.add_post('/', self.handle, name='handle')

    async def init(self):
        app = web.Application(loop=self.loop)
        self.setup_routes(app, self.handler)
        return app

    def main(self):
        app = self.loop.run_until_complete(self.init())
        host, port = self.conf.host, self.conf.port
        web.run_app(app, host=host, port=port)

    def get_config(self, argv=None):
        parser = argparse.ArgumentParser(
            description='cl-orch')

        parser.add_argument('--host',
                            type=str,
                            help='Define the host address (default: None)')

        parser.add_argument('--port',
                            type=str,
                            help='Define the host port (default: None)')

        parser.add_argument('--debug',
                            action='store_true',
                            help='Define the app logging mode (default: False)')

        # options, unknown = ap.parse_known_args(argv)
        config = parser.parse_args(argv)
        return config

    async def send(self, url, data):
        async def post(session, url, data):
            async with session.post(url, json=data) as response:
                print(response.status)
                resp_text = await response.text()
                return resp_text

        async with aiohttp.ClientSession() as session:
            html = await post(session, url, data)
            return html


if __name__ == '__main__':
    app = App()
    app.main()