import os
import json
import time
import logging
import asyncio
import concurrent.futures
import subprocess
from datetime import datetime
from functools import partial
import docker
import psutil as ps
import platform as pl

from subprocess import check_output, CalledProcessError


from umbra.common.scheduler import Handler


logger = logging.getLogger(__name__)


class Tool():
    def __init__(self, id_, name):
        self.is_process = False
        self.id = id_
        self.name = name
        self.out_queue = None
        self.stimulus = None
        self.opts = None
        self.action = None
        self.uuid = None
        self.parameters = {}
        self.metrics = {}
        self.cfg()
       
    async def process_call(self):
        """Performs the async execution of cmd in a subprocess
        
        Arguments:
            cmd {string} -- The full command to be called in a subprocess shell
        
        Returns:
            dict -- The output of the cmd execution containing stdout and stderr fields
        """
        cmd = self.stimulus
        logger.debug(f"Calling subprocess command: {cmd}")
        out = {}
        try:
            proc = await asyncio.create_subprocess_shell(
                cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await proc.communicate()

            out = {
                "stdout": stdout.decode("utf-8"),
                "stderr": stderr.decode("utf-8"),
            }

        except OSError as excpt:
            logger.debug(f"Could not call cmd {cmd} - exception {excpt}")

            out = {
                "stdout": None,
                "stderr": proc.exception(),
            }
        except asyncio.CancelledError:
            logger.debug("cancel_me(): call task cancelled")
            raise

        finally:
            return out

    async def function_call(self):
        function_call = self.stimulus
        loop = asyncio.get_event_loop()
        with concurrent.futures.ProcessPoolExecutor() as pool:
            output = await loop.run_in_executor(pool, function_call)

        return output

    async def call(self):
        if self.is_process:
            results = await self.process_call()
        else:
            results = await self.function_call()
        
        self.parser(results)
        return self.metrics

    def cfg(self):
        pass

    def options(self, **kwargs):
        pass

    def parser(self, results):
        pass
        
    def init(self, action):
        self.action = action
        parameters = self.action.get("parameters")
        options = self.serialize(**parameters)
        self.options(**options)

    def serialize(self, **kwargs):
        options = {}
        for k, v in kwargs.items():
            if k in self.parameters:
                options[self.parameters[k]] = v
            else:
                logger.info("serialize option not found %s", k)
        return options

    def flush(self, url, metrics):
        data = {
            "type": "events",
            "event": "metrics",
            "group": "infrastructure",
            "live": True,
            "metrics": metrics,
            "ev": self.ev,
        }       
        ok = self.send(url, data)
        logger.debug("Live metrics flush ack %s", ok)

    def send(self, url, data, **kwargs):
        headers = {'Content-Type': 'application/json'}
        json_data = json.dumps(data)
        try:
            response = requests.post(url, headers=headers, data=json_data, **kwargs)
        except requests.RequestException as exception:
            logger.info('Requests fail - exception %s', exception)
            response = None
        else:
            try:
                response.raise_for_status()
            except Exception:
                response = None
        finally:
            return response


class Tcpreplay(Tool):
    def __init__(self):
        Tool.__init__(self, 1, "tcpreplay")
        self._instances_folder = '/mnt/pcaps/'

    def cfg(self):
        params = {
            'interface':'-i',
            'duration':'--duration',
            'speed':'-t',
            'timing':'-T',
            'preload':'-K',
            'loop':'-l',
            'pcap':'-f'
        }
        self.parameters = params
        self.cmd = "tcpreplay"

    def filepath(self, filename):
        _filepath = os.path.normpath(os.path.join(
            self._instances_folder, filename))
        return _filepath

    def options(self, **options):
        cmd = [self.cmd]
        opts = []
 
        for k,v in options.items():
            if k == '-t':
                opts.extend([k])
            elif k == '-K':
                opts.extend([k])
            else:
                if k != '-f':
                    opts.extend([k,v])

        opts.append('-q')
        
        if '-f' in options:
            pcap_value = options.get('-f')
            pcap_path = self.filepath(pcap_value)
            opts.append(pcap_path)

        cmd.extend(opts)

        self.is_process = True
        self.stimulus = " ".join(cmd)

    def parser(self, out):
        output = out.get("stdout")

        lines = output.split('\n')
        if len(lines) > 1:
            actual = [line for line in lines if 'Actual' in line]
            actual_info = actual.pop().split()
            metrics = {
                'packets': int(actual_info[1]),
                'time': float(actual_info[-2]),
            }

        self.metrics = {
            "uuid": self.uuid,
            "metrics": metrics
        }


class Ping(Tool):
    def __init__(self):
        Tool.__init__(self, 3, "ping")

    def cfg(self):
        params = {
            'interval':'-i',
            'duration':'-w',
            'packets':'-c',
            'frame_size':'-s',
            'target':'target',
        }
        self.parameters = params
        self.cmd = "ping"

    def options(self, **kwargs):
        cmd = [self.cmd]
        opts = []

        for k, v in kwargs.items():
            if k == 'target':
                continue
            else:
                opts.extend([k, v])
        if 'target' in kwargs:
            opts.append(kwargs['target'])

        cmd.extend(opts)

        self.is_process = True
        self.stimulus = " ".join(cmd)

    def parser(self, out):
        metrics = []

        logger.info(f"Ping output {out}")

        output = out.get("stdout")

        lines = [line for line in output.split('\n') if line.strip()]
        if len(lines) > 1:
            rtt_indexes = [i for i, j in enumerate(lines) if 'rtt' in j]
            if not rtt_indexes:
                rtt_indexes = [i for i, j in enumerate(lines) if 'round-trip' in j]
            if rtt_indexes:
                rtt_index = rtt_indexes.pop()
                rtt_line = lines[rtt_index].split(' ')
                loss_line = lines[rtt_index-1].split(' ')
                rtts = rtt_line[3].split('/')
                rtt_units = rtt_line[4]
                if 'time' in loss_line:
                    pkt_loss = loss_line[-5][0]
                    pkt_loss_units = loss_line[-5][-1]
                else: 
                    pkt_loss = loss_line[-3][0]
                    pkt_loss_units = loss_line[-3][-1]
                metrics = {
                    'latency':{
                        'rtt_min': float(rtts[0]),
                        'rtt_avg': float(rtts[1]),
                        'rtt_max': float(rtts[2]),
                        'rtt_mdev': float(rtts[3]),
                        'units': rtt_units},
                    'frame_loss':{
                        'frames': float(loss_line[0]),
                        'frame_loss': float(pkt_loss),
                        'units': pkt_loss_units,
                    }
                }
            else:
                metrics = {"error parsing ping results"}               

        self.metrics = {
            "uuid": self.uuid,
            "metrics": metrics
        }


class Iperf3(Tool):
    def __init__(self):
        Tool.__init__(self, 2, "iperf3")

    def cfg(self):
        params = {
            'port':'-p',
            'duration':'-t',
            'protocol':'-u',
            'server':'-s',
            'client':'-c',
            'rate':'-b'
        }
        self.parameters = params
        self.cmd = "iperf3"

    def options(self, **options):
        cmd = [self.cmd]
        opts = []
        stop = False
        timeout = 0

        server = options.get('-s', None)
        client = options.get('-c', False)
        
        if server:
            opts.extend( ['-c', server] )                
            time.sleep(1)
        if not client or client == 'false' or client == 'False':
            opts.extend( ['-s'] )                
            stop = True
        
        port = options.get('-p', '9030')
        opts.extend( ['-p', port] )                
        
        timeout = float(options.get('-t', 0))
        if timeout and not stop:
            opts.extend( ['-t', str(timeout+1)] )
            timeout = 0

        proto = options.get('-u', None)
        if proto == 'udp':
            if not stop:
                opts.extend(['-u'])

        rate = options.get('-b', None)
        if rate and not stop:
            opts.extend( ['-b', rate] )
            
        opts.extend(['-f','m'])
        opts.append('-J')

        cmd.extend(opts)

        self.is_process = True
        self.stimulus = " ".join(cmd)

    def parser(self, out):
        metrics = []

        output = out.get("stdout")

        try:
            out = json.loads(output)
        except ValueError:
            logger.debug('iperf3 json output could not be decoded')
            out = {}
        else:
            end = out.get("end", None)
            if end:
                if 'sum_sent' in end:
                    metrics = end.get('sum_sent')
                if 'sum' in end:
                    metrics = end.get('sum')
        finally:

            self.metrics = {
                "uuid": self.uuid,
                "metrics": metrics
            }


class Tools:
    TOOLS = [
        Ping,
        Tcpreplay, 
        Iperf3,
    ]

    def __init__(self):
        self.toolset = {}
        self.load_tools()
        self.handler = Handler()
        
    def load_tools(self):
        for tool_cls in self.TOOLS:
            tool_instance = tool_cls()
            tool_name = tool_instance.name
            self.toolset[tool_name] = tool_instance
        logger.debug("loaded toolset")

    def build_calls(self, actions):
        logger.info("Building actions into calls")
        calls = {}

        for action in actions:
            tool_name = action.get("tool")

            if tool_name in self.toolset:

                action_id = action.get("id")
                action_sched = action.get("schedule", {})

                tool = self.toolset[tool_name]               
                tool.init(action)
                action_call = tool.call()
                
                calls[action_id] = (action_call, action_sched)

            else:
                logger.info(
                    f"Could not locate action tool name {tool_name}"
                    f" into set of tools {self.toolset.keys()}"
                )

        return calls

    def build_outputs(self, outputs):        
        data = {
            "event": "metrics",
            "metrics": outputs,
        }
        logger.info(f"data: {data}")
        return data

    async def handle(self, instruction):
        actions = instruction.get("actions")
        calls = self.build_calls(actions)
        results = await self.handler.run(calls)
        outputs = self.build_outputs(results)
        logger.info(f"Finished handling instruction actions")
        logger.debug(f"{outputs}")
        return outputs