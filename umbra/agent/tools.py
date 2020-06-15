import os
import logging
import json
import time

from umbra.agent.procs import Runner

logger = logging.getLogger(__name__)


class Tool():
    def __init__(self, id_, name):
        self.id = id_
        self.name = name
        self.cmd = None
        self.parameters = {}
        self.metrics = {}
        self.cfg()

    def cfg(self):
        pass

    def serialize(self, **kwargs):
        options = {}
        for k, v in kwargs.items():
            if k in self.parameters:
                options[self.parameters[k]] = v
            else:
                logger.info("serialize option not found %s", k)
        return options

    def options(self, kwargs):
        pass

    def parse(self, output):
        pass


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

    def options(self, kwargs):
        cmd = [self.cmd]
        options = self.serialize(**kwargs)
        opts = []
        stop = False
        timeout = 0
 
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
        stm = {'cmd': cmd, 'stop': stop, 'timeout': timeout}
        return stm

    def filepath(self, filename):
        _filepath = os.path.normpath(os.path.join(
            self._instances_folder, filename))
        return _filepath

    def parse(self, out):
        lines = out.split('\n')
        if len(lines) > 1:
            actual = [line for line in lines if 'Actual' in line]
            actual_info = actual.pop().split()
            metrics = {
                'packets': int(actual_info[1]),
                'time': float(actual_info[-2]),
            }
        self.metrics = metrics
        return self.metrics


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

    def options(self, kwargs):
        cmd = [self.cmd]
        options = self.serialize(**kwargs)
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
        stm = {'cmd': cmd, 'stop': stop, 'timeout': timeout}
        return stm

    def parse(self, output):
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
            self.metrics = metrics
            return self.metrics


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

    def options(self, kwargs):
        cmd = [self.cmd]
        options = self.serialize(**kwargs)
        opts = []
        stop = False
        timeout = 0

        for k, v in options.items():
            if k == 'target':
                continue
            else:
                opts.extend([k, v])
        if 'target' in options:
            opts.append(options['target'])

        cmd.extend(opts)
        stm = {'cmd': cmd, 'stop': stop, 'timeout': timeout}
        return stm

    def parse(self, output):
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
            self.metrics = metrics
        return self.metrics


class Server(Tool):
    def __init__(self):
        Tool.__init__(self, 4, "server")
        self.default_address = "0.0.0.0:9015"
        self.default_folder = "/mnt/files/"

    def cfg(self):
        params = {
            'folder':'folder',
            'duration':'duration'
        }
        self.parameters = params
        self.cmd = "caddy"

    def options(self, kwargs):
        cmd = [self.cmd]
        options = self.serialize(**kwargs)
        stop = False
        timeout = 0

        if 'duration' in options:
            timeout = options['duration']

        if 'folder' in options:
            self.default_folder = options['folder']

        where = self.dump_opts(options)
        cmd.extend(['-conf', where])
        stm = {'cmd': cmd, 'stop': stop, 'timeout': timeout}
        return stm

    def dump_opts(self, options):
        where = "/tmp/caddy_conf"
        opts = [
            options.get('address', self.default_address) + '\n', 
            "root " + options.get('folder', self.default_folder) + '\n',
        ]
        with open(where, "+w") as f:
            for opt in opts:
                f.write(opt)
            # f.writelines(opts)
        return where

    def parse(self, output):
        return self.metrics


class Client(Tool):
    def __init__(self):
        Tool.__init__(self, 5, "client")

    def cfg(self):
        params = {
            'url': 'url'            
        }
        self.parameters = params
        self.cmd = "wget"

    def options(self, kwargs):
        cmd = [self.cmd]
        options = self.serialize(**kwargs)
        opts = []
        stop = False
        timeout = 0

        if 'url' in options:
            opts.extend(['-o', options['url']])

        for k, v in options.items():
            if k == 'url':
                continue
            else:
                opts.extend([k, v])


        cmd.extend(opts)
        stm = {'cmd': cmd, 'stop': stop, 'timeout': timeout}
        return stm

    def parse(self, output):
        print(output)
        return self.metrics


class Tools(Runner):
    TOOLS = [
        Tcpreplay,
        Iperf3,
        Ping,
        Server,
        Client,
    ]

    TOOL_IDS = enumerate(TOOLS,1)

    def __init__(self):
        Runner.__init__(self)
        self.toolset = {}
        self.load_tools()

    def load_tools(self):
        for tool_cls in self.TOOLS:
            tool_instance = tool_cls()
            tool_id = tool_instance.id
            self.toolset[tool_id] = tool_instance
        logger.debug("loaded toolset")

    def build_stimulus(self, instructions):
        logger.debug("build stimulus from instructions")
        logger.debug(instructions)
        stimulus = {}
        for _id,instruction in instructions.items():
            tool_id = instruction.get("tool-id")
            if tool_id in self.toolset:
                tool = self.toolset[tool_id]
                parameters = instruction.get("parameters")
                tool_cmd = tool.options(parameters)
                stimulus[_id] = tool_cmd
                logger.debug("Stimulus with tool-name %s; parameters %s", tool.name, parameters)
        return stimulus

    def parse_outputs(self, instructions, outputs):
        evals = {}
        for _id, output in outputs.items():
            ack, data = output
            stimulus = instructions.get(_id)
            tool_id = stimulus.get("tool-id")
            tool = self.toolset[tool_id]
            # logger.info("Ack %s - Data %s", ack, data)
            if ack == 'ok':
                metrics = tool.parse(data)
                result = {'metrics':metrics}
                logger.debug("Output OK: tool %s metrics %s", tool.name, metrics)
            else:
                result = {'error': data}
                logger.debug("Output Error: tool %s metrics %s", tool.name, data)
            evals[_id] = result
        return evals
    
    def act(self, instructions):
        stimulus = self.build_stimulus(instructions)
        outputs = self.run(stimulus)
        evals = self.parse_outputs(instructions, outputs)
        return evals

    def workflow(self, data):
        output = []
        instructions = data.get("instructions", None)
        if instructions:
            _to = data.get("callback", None)
            _ev = data.get("ev", None)
            _evals = self.act(instructions)
            
            data = {
                "type": "events",
                "event": "metrics",
                "group": "calls",
                "evals": _evals,
                "ev": _ev,
            }

            msg = {
                'to': _to,
                'data': data,
            }
            output.append(msg)
        return output
    