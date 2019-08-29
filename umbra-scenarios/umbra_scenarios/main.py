import sys
import logging
import logging.config
import gevent
import json 
import requests
import argparse
# from urllib.urlparse import urlparse
from urlparse import urlparse
from flask import Flask, request, make_response
from flask_restful import Api, Resource
from gevent.pywsgi import WSGIServer
from gevent.queue import Empty, Queue


from umbra_scenarios.topo import Experiment

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


class Resources(Resource):
    settings = {
        'content-type':'application/json'
    }
    api = Api()

    def __init__(self, **kwargs):
        self.handlers = kwargs['handlers']
        self.content_type = kwargs['content-type']
        Resources.settings['content-type'] = self.content_type
        Resources.api = kwargs['api']

    def parse_path(self, path):
        prefix, call = '', ''
        if path:
            try:
                prefix, call = path.rsplit('/', 1)
            except:
                prefix = path
                call = ""
            call = call.replace('-', '_')
            prefix = prefix.replace('-', '_')
        return prefix, call

    @api.representation(settings['content-type'])
    def post(self, path=None):
        method = 'post'
        prefix, call = self.parse_path(path)
        data = request.data
        address = request.remote_addr
        handler = self.handlers[method]
        ack, reply = handler((address, prefix, call, data))
        code = 200 if ack else 500
        resp = make_response(reply, code)
        resp.headers['Content-Type'] = self.content_type
        return resp

    @api.representation(settings['content-type'])
    def get(self, path=None):
        method = 'get'
        prefix, call = self.parse_path(path)
        data = request.data
        address = request.remote_addr
        handler = self.handlers[method]
        ack, reply = handler((address, prefix, call, data))
        code = 200 if ack else 500
        resp = make_response(reply, code)
        resp.headers['Content-Type'] = self.content_type
        return resp

    @api.representation(settings['content-type'])
    def put(self, path=None):
        method = 'put'
        prefix, call = self.parse_path(path)
        data = request.data
        address = request.remote_addr
        handler = self.handlers[method]
        ack, reply = handler((address, prefix, call, data))
        code = 200 if ack else 500
        resp = make_response(reply, code)
        resp.headers['Content-Type'] = self.content_type
        return resp

    @api.representation(settings['content-type'])
    def delete(self, path=None):
        method = 'delete'
        prefix, call = self.parse_path(path)
        data = request.data
        address = request.remote_addr
        handler = self.handlers[method]
        ack, reply = handler((address, prefix, call, data))
        code = 200 if ack else 500
        resp = make_response(reply, code)
        resp.headers['Content-Type'] = self.content_type
        return resp


class WebServer():
    def __init__(self, url, handlers,
                 content_type='application/json'):
        self.path = "/<path:path>"
        self.prefix = '/'
        self.app = app = Flask(__name__)
        self.api = Api(app)
        self.url = url
        self.host = urlparse(self.url).hostname
        self.port = urlparse(self.url).port
        self.resource = {
            'class': Resources,
            'path': self.path,
            'prefix': self.prefix,
        }
        self.settings = {
            'handlers': handlers,
            'content-type': content_type,
            'api': self.api,
        }
        self.server = None

    def add_resources(self, resource, **kwargs):
        self.api.add_resource(resource['class'], resource['path'], resource['prefix'],
                              resource_class_kwargs=kwargs)

    def init(self, debug=False, reloader=False):
        self.add_resources(self.resource, **self.settings)
        self.server = WSGIServer((self.host, self.port), self.app)
        self.server.serve_forever()


class WebClient():
    headers = {'Content-Type': 'application/json'}

    def send_msg(self, _type, url, message, **kwargs):
        response = None
        try:
            if _type == 'post':
                response = requests.post(url, headers=WebClient.headers, data=message, **kwargs)
            elif _type == 'put':
                response = requests.put(url, headers=WebClient.headers, data=message, **kwargs)
            elif _type == 'get':
                response = requests.get(url, headers=WebClient.headers, data=message, **kwargs)
            else:
                response = requests.delete(url, headers=WebClient.headers, data=message, **kwargs)
        except requests.RequestException as exception:
            logger.info('Requests fail - exception %s', exception)
            response = None
        finally:
            reply = self.__process_msg_response(response)
            logger.info('Requests - response %s', response)
            if reply:
                return reply.text
            return reply

    def __process_msg_response(self, response):
        try:
            if response:
                response.raise_for_status()
        except Exception as exception:
            logging.info("Response exception %s", exception)
            response = None
        finally:
            return response


class Playground:
    def __init__(self):
        self.exp_topo = None
        self.running = False
        self.clear()

    def start(self, run_id, scenario):
        instance = 500
        logger.info("received scenario %s", scenario)
        self.exp_topo = Experiment(instance, scenario)
        self.exp_topo.build()
        hosts_info = self.exp_topo.start()
        self.running = True
        logger.info("expo_topo running %s", self.running)
        logger.info("hosts info %s", hosts_info)
        ack = {
            'running': self.running,
            'instance': instance,
            'management': hosts_info, 
        }
        return ack

    def stop(self):
        self.exp_topo.stop()
        self.running = False
        logger.info("expo_topo running %s", self.running)
        ack = {'running': self.running}
        return ack

    def update(self, events):
        ack = self.exp_topo.update(events)
        body = {'updates': ack}
        return body
        
    def alive(self):
        return self.running

    def clear(self):
        exp = Experiment(0, None)
        exp.mn_cleanup()
        logger.info("Experiments cleanup OK")


class Scenario:
    def __init__(self):
        self._ids = 0
        self.conf = None
        self.in_q = Queue()
        self.handlers = {
            'post':self.post_handler,
        }
        self.playground = Playground()
        self.client = WebClient()
        self.server = None

    def post_handler(self, msg):
        address, prefix, request, data = msg
        logger.info("post_handler - address %s, prefix %s, request %s",
                    address, prefix, request)
        self.in_q.put(data)
        return True, 'Ack'
        
    def handle(self, msg):
        outputs = []

        cmd = None
        msg_type = msg.get("type")

        if msg_type == "deploy":
            # msg_id = msg.get("id")
            cmd = msg.get("request")
            continuous = msg.get("continuous", None)
            callback = msg.get("callback")
            data = msg.get("scenario")
            logger.info("received msg: request %s, continuous %s, callback %s", 
                        cmd, continuous, callback)
                
            built = dict()
            # built["id"] = msg_id
            built["type"] = "built"
            built["to"] = callback

            if continuous:
                if self.playground.alive():
                    self.playground.stop()

        if msg_type == "events":
            cmd = "update"
            data = msg.get("events")
                    
        if cmd == "start":
            start_info = self.playground.start(self._ids, data)
            self._ids += 1
            built["data"] = start_info
            outputs.append(built)
        elif cmd == "stop":
            if self.playground.alive():
                stop_info = self.playground.stop()
                built["data"] = stop_info
                outputs.append(built)
        elif cmd == "update":
            if self.playground.alive():
                update_info = self.playground.update(data)
                logger.info("Handle update_info %s", update_info)

                # built["data"] = update_info
                # outputs.append(built)
        else:
            logger.info("Handle no cmd in request data")
        return outputs

    def serve(self):
        self.server = WebServer(self.conf.url, self.handlers)
        logger.info("Scenarios Started")
        _jobs = self._create_jobs()
        gevent.joinall(_jobs)
        
    def _create_jobs(self):
        web_server_thread = gevent.spawn(self.server.init)
        msgs_loop = gevent.spawn(self._process_msgs)
        jobs = [web_server_thread, msgs_loop]
        return jobs

    def send(self, url, data, method='post'):
        logger.info("sending msg to %s - data %s", url, data)
        answer = self.client.send_msg(method, url, data)
        return answer

    def exit(self, outputs):
        if outputs:
            for output in outputs:
                url = output["to"]
                del output["to"]
                output_json = json.dumps(output)
                if url:
                    exit_reply = self.send(url, output_json)
                    logger.info("exit_reply %s", exit_reply)
                else:
                    logger.info("No callback provided for %s", output_json)
        else:
            logger.info("nothing to output")

    def _process_msgs(self):
        while True:
            try:
                data = self.in_q.get()
            except Empty:
                continue
            else:
                logger.info(data)
                # msg = Message.parse(data, rpc_map)                
                msg = json.loads(data)
                logger.info(msg)
                if msg:                
                    outputs = self.handle(msg)
                    self.exit(outputs)
                else:
                    logger.info("could not parse data %s", data)

    def get_config(self, argv=None):
        parser = argparse.ArgumentParser(
            description='cl-scenarios')

        parser.add_argument('--url',
                            type=str,
                            help='Define the url (default: None)')

        parser.add_argument('--debug',
                            action='store_true',
                            help='Define the app logging mode (default: False)')

        # options, unknown = ap.parse_known_args(argv)
        config = parser.parse_args(argv)
        return config

    def logs(self, conf):
        filename = "/tmp/cl-scenarios.log"
        Logs(filename, debug=conf.debug)

    def run(self, argv):
        self.conf = self.get_config(argv)
        self.logs(self.conf)
        self.serve()


def main():
    sc = Scenario()
    sc.run(sys.argv[1:])
