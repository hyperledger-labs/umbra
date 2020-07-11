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
from umbra.common.protobuf.umbra_pb2 import Evaluation
from umbra.common.protobuf.umbra_grpc import BrokerStub


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
        self.output = {}
        self.parameters = {}
        self.metrics = {}
        self._tstart = None
        self._tstop = None
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
        self._tstart = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        if self.is_process:
            results = await self.process_call()
        else:
            results = await self.function_call()

        self._tstop = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        
        self.parser(results)
        return self.metrics

    def get_uuid(self):
        return self.uuid

    def source(self):
        if type(self.stimulus) is str:
            stimulus = self.stimulus
        else:
            stimulus = "agent-function-" + self.name
        
        source = {
            'call': stimulus,
            'name': self.name,
        }
        return source

    def timestamp(self):
        """Builds a dict indicating the
        time when the tool started and stopped
        its execution

        Returns:
            dict -- As below
        """
        ts = {
            "start": self._tstart,
            "stop": self._tstop,
        }
        return ts

    def cfg(self):
        pass

    def options(self, **kwargs):
        pass

    def parser(self, results):
        pass
        
    def init(self, action):
        self.action = action
        self.uuid = action.get('id')
        self.output = action.get('output', {})
        parameters = self.action.get("parameters", {})
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
        }       


class Tcpreplay(Tool):
    def __init__(self):
        Tool.__init__(self, 1, "tcpreplay")
        self._instances_folder = '/mnt/pcaps/'

    def cfg(self):
        params = {
            'folder': 'folder',
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
                if k != '-f' and k != 'folder':
                    opts.extend([k,v])

        opts.append('-q')
        
        if '-f' in options:
            if 'folder' in options:
                self._instances_folder = options.get('folder')
            pcap_value = options.get('-f')
            pcap_path = self.filepath(pcap_value)
            opts.append(pcap_path)

        cmd.extend(opts)

        self.is_process = True
        self.stimulus = " ".join(cmd)

    def parser(self, out):
        output = out.get("stdout")

        _eval = []
        lines = output.split('\n')
        if len(lines) > 1:
            actual = [line for line in lines if 'Actual' in line]
            actual_info = actual.pop().split()
            
            # eval_info = {
            #     'packets': int(actual_info[1]),
            #     'time': float(actual_info[-2]),
            # }

            m1 = {
                "name": "packets",
                "type": "int",
                "unit": "packets",
                "scalar": int(actual_info[1]),
            }

            m2 = {
                "name": "time",
                "type": "float",
                "unit": "seconds",
                "scalar": float(actual_info[-2]),
            }

            _eval = [m1, m2]

        self.metrics = {
            "uuid": self.uuid,
            "metrics": _eval
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

    def parser(self, output):
        out = output.get('stdout')

        _eval = {}
        lines = [line for line in out.split('\n') if line.strip()]
        
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
                
                m1 = {
                    "name": "rtt_min",
                    "type": "float",
                    "unit": rtt_units,
                    "scalar": float(rtts[0].replace(",", ".")),
                }
                
                m2 = {
                    "name": "rtt_avg",
                    "type": "float",
                    "unit": rtt_units,
                    "scalar": float(rtts[1].replace(",", ".")),
                }

                m3 = {
                    "name": "rtt_max",
                    "type": "float",
                    "unit": rtt_units,
                    "scalar": float(rtts[2].replace(",", ".")),
                }

                m4 = {
                    "name": "rtt_mdev",
                    "type": "float",
                    "unit": rtt_units,
                    "scalar": float(rtts[3].replace(",", ".")),
                }

                m5 = {
                    "name": "frame_loss",
                    "type": "float",
                    "unit": pkt_loss_units,
                    "scalar": float(pkt_loss),
                }

                _eval = [m1, m2, m3, m4, m5]

        self.metrics = {
            "uuid": self.uuid,
            "metrics": _eval
        }


class Iperf3(Tool):
    def __init__(self):
        Tool.__init__(self, 2, "iperf3")
        self._server = False

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
        
        info = options.get('info', None)
        if info:
            opts.extend(['info', info])

        server = options.get('-s', None)
        client = options.get('-c', False)
        
        if server:
            opts.extend( ['-c', server] )                
            time.sleep(1)

        if not client or client == 'false' or client == 'False':
            opts.extend( ['-s'] )                
            stop = True
            self._server = True
        
        port = options.get('-p', '9030')
        opts.extend( ['-p', port] )                
        
        timeout = float(options.get('-t', 0))
        if timeout and not stop:
            opts.extend( ['-t', str(timeout)] )
            timeout = 0
        
        if stop:
            timeout += 2

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

    def parser(self, output):
        out = output.get("stdout")

        _eval = []
        try:
            out = json.loads(out)
        except ValueError:
            logger.debug('iperf3 json output could not be decoded')
            out = {}
        else:
            end = out.get("end", None)
            
            if end:
                if 'sum_sent' in end:
                    _values = end.get('sum_sent')
                elif 'sum' in end:
                    _values = end.get('sum')
                else:
                    _values = {}

                if not self._server and _values:
            
                    m1 = {
                        "name": "bits_per_second",
                        "type": "float",
                        "unit": "bits_per_second",
                        "scalar": float(_values.get("bits_per_second")),
                    }

                    m2 = {
                        "name": "jitter_ms",
                        "type": "float",
                        "unit": "ms",
                        "scalar": float(_values.get("jitter_ms")),
                    }

                    m3 = {
                        "name": "bytes",
                        "type": "int",
                        "unit": "bytes",
                        "scalar": int(_values.get("bytes")),
                    }


                    m4 = {
                        "name": "lost_packets",
                        "type": "int",
                        "unit": "packets",
                        "scalar": int(_values.get("lost_packets")),
                    }

                    m5 = {
                        "name": "lost_percent",
                        "type": "float",
                        "unit": "%",
                        "scalar": float(_values.get("lost_percent")),
                    }

                    m6 = {
                        "name": "packets",
                        "type": "int",
                        "unit": "packets",
                        "scalar": int(_values.get("packets")),
                    }


                    _eval = [m1, m2, m3, m4, m5, m6]
                    
        finally:
            self.metrics = {
                "uuid": self.uuid,
                "metrics": _eval
            }


class Tools:
    TOOLS = [
        Ping,
        Tcpreplay, 
        Iperf3,
    ]

    def __init__(self):
        self.toolset = {}
        self.tools_instances = {}
        self.load_tools()
        self.handler = Handler()
        
    def load_tools(self):
        for tool_cls in self.TOOLS:
            tool_instance = tool_cls()
            tool_name = tool_instance.name
            self.toolset[tool_name] = tool_cls
        logger.debug("loaded toolset")

    def build_calls(self, actions):
        logger.info("Building actions into calls")
        calls = {}

        for action in actions:
            tool_name = action.get("tool")

            if tool_name in self.toolset:

                action_id = action.get("id")
                action_sched = action.get("schedule", {})

                tool_cls = self.toolset[tool_name]
                tool = tool_cls()              
                tool.init(action)
                action_call = tool.call
                
                calls[action_id] = (action_call, action_sched)

                tool_uuid = tool.get_uuid()
                self.tools_instances[tool_uuid] = tool

            else:
                logger.info(
                    f"Could not locate action tool name {tool_name}"
                    f" into set of tools {self.toolset.keys()}"
                )

        return calls

    def build_outputs(self, outputs):        
        logger.info(f'build outputs: {outputs}')
        data = []
        uuid_end = []

        for uuid,output in outputs.items():
            tool = self.tools_instances.get(uuid)
            tool_eval = {
                'id': uuid,
                'source': tool.source(),
                'timestamp': tool.timestamp(),
                'metrics': output.get('metrics', []),
            }
            data.append(tool_eval)

        for uuid in uuid_end:
            del self.tools_instances[uuid]

        return data

    async def handle(self, instruction):
        actions = instruction.get("actions")
        calls = self.build_calls(actions)
        results = await self.handler.run(calls)
        evals = self.build_outputs(results)
        logger.info(f"Finished handling instruction actions")
        snap = {
            "id": instruction.get('id'),
            "evaluations": evals,
        }
        logger.debug(f"{snap}")
        return snap