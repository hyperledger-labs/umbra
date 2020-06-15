import os
import logging
import json
import time
from datetime import datetime

import asyncio
import requests
import concurrent.futures

import subprocess

import docker
import psutil as ps
import platform as pl
from subprocess import CalledProcessError, check_output


logger = logging.getLogger(__name__)


class Tool():
    def __init__(self, id_, name):
        self.id = id_
        self.name = name
        self.out_queue = None
        self.cmd = None
        self.opts = None
        self.stimulus = None
        self.uuid = None
        self.ev = None
        self.parameters = {}
        self.metrics = {}
        self.cfg()

    def call(self):
        return self.cmd

    def args(self):
        return self.opts

    def cfg(self):
        pass

    def options(self, **kwargs):
        pass

    def parser(self, results):
        pass

    def outputs(self, results):
        self.parser(results)
        return self.metrics

    def init(self, ev, uuid, stimulus):
        self.ev = ev
        self.uuid = uuid
        self.stimulus = stimulus
        specs = self.stimulus.get("parameters")
        self.options(**specs)

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

    def start_process(self, args, stop=False, timeout=60):
        return_code = 0
        out, err = '', None

        try:
            p = subprocess.Popen(args,
                stdin = subprocess.PIPE,
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE,
                )
            self.process = p
            if stop:
                if self.stop_process(timeout):
                    out, err = p.communicate()
                    return_code = p.returncode
                else:
                    return_code = -1
                    err = 'ERROR: Process not defined'
            else:
                out, err = p.communicate()
                return_code = p.returncode
        except Exception as e:
            return_code = -1
            # logger.debug('ERROR: exception %s', e)
            err = 'ERROR: exception OSError'
        finally:
            # logger.debug('process stopped')
            if return_code != 0:
                queue_answer = err
            else:
                queue_answer = out
            self.process = None
            result = (return_code, queue_answer)
            return result

    def stop_process(self, timeout):
        if self.process:
            time.sleep(timeout)
            self.process.kill()
            logger.info('process stopped %s', self.process.pid)
            self.process = None
            return True
        return False


class MonDummy(Tool):
    def __init__(self):
        Tool.__init__(self, 11, 'dummy')
        
    def cfg(self):
        params = {
            'interval': 'interval',
            'duration': 'duration',
        }
        self.parameters = params
        self.cmd = 'uname'

    def monitor(self, opts):
        metrics = []
        interval = opts.get("interval")
        duration = opts.get("duration")
        live = self.stimulus.get("live", False)
        url = self.stimulus.get("url", None)

        past = datetime.now()
        while True:
            current = datetime.now()
            _time = {'timestamp': current.strftime('%Y-%m-%dT%H:%M:%S.%fZ')}
            seconds = (current-past).total_seconds()
            if seconds > duration:
                break
            else:
                # measurement = {seconds:"self.run([self.cmd])"}
                (ack, result) = self.start_process([self.cmd])
                measurement = {'result': result}
                measurement.update(_time)
                metrics.append(measurement)
                
                if live:
                    self.flush(url, measurement)

                time.sleep(interval)

        results = {
            "uuid": self.uuid,
            "metrics": metrics
        }
        return results

    def options(self, **kwargs):
        options = self.serialize(**kwargs)
        self.cmd = self.monitor
        self.opts = options

    def parser(self, out):
        self.metrics = out
        

class MonProcess(Tool):

    def __init__(self):
        Tool.__init__(self, 1, 'process')
        self._first = True
        self._command = None

    def cfg(self):
        params = {
            'interval': 'interval',
            'name': 'name',
            'pid': 'pid',
            'duration': 'duration',
        }
        self.parameters = params
        self.cmd = ""

    def _get_process_info(self):
        info = {}
        info['name'] = self._p.name()
        info['exe'] = self._p.exe()
        info['cwd'] = self._p.cwd()
        info['status'] = self._p.status()
        info['username'] = self._p.username()
        info['create_time'] = self._p.create_time()
        return info

    def _get_process_cpu(self, tm, prev_info):
        cpu_stats = {}
        cpu_stats["cpu_num"] = self._p.cpu_num()

        # cpu_affinity
        # affinity = self._p.cpu_affinity()

        # cpu_stats["cpu_affinity"] = ""
        # for index in range(len(affinity)):
        #     if cpu_stats["cpu_affinity"] == "":
        #         cpu_stats["cpu_affinity"] = str(affinity[index])
        #     else:
        #         cpu_stats["cpu_affinity"] = cpu_stats["cpu_affinity"] + "," + str(affinity[index])

        # cpu_percent
        cpu_stats["cpu_percent"] = self._p.cpu_percent(interval=0.5)

        # user_time, system_time
        cpu_times = self._p.cpu_times()
        user_time, system_time = cpu_times.user, cpu_times.system

        if self._first == False:
            cpu_stats["user_time"] = (user_time - prev_info["user_time"]) / (tm - prev_info["time"])
            cpu_stats["system_time"] = (system_time - prev_info["system_time"]) / (tm - prev_info["time"])

        cpu_stats["user_time"] = user_time
        cpu_stats["system_time"] = system_time
        cpu_stats["num_threads"] = self._p.num_threads() * 1.0

        return cpu_stats
        # cpu = {}
        # cpu['percent'] = self._p.cpu_percent()
        # cpu['affinity'] = self._p.cpu_affinity()
        # cpu['cputimes'] = self._p.cpu_times().__dict__
        # cpu['nice'] = self._p.nice()
        # ts = self._p.threads()
        # ts = [t.__dict__ for t in ts]
        # cpu['threads'] = ts
        # return cpu

    def _get_process_mem(self):
        mem_stats = {}
        mem_stats["mem_percent"] = self._p.memory_percent()
        return mem_stats

        # mem = {}
        # mem['percent'] = self._p.memory_percent()
        # mem['swap'] = self._p.memory_info().__dict__

    def _get_process_storage(self, tm, prev_info):
        io_stats = {}
        # if os.getuid() == 0:
        io_counters = self._p.io_counters()

        if self._first == False:
            io_stats["read_count"] = (io_counters.read_count * 1.0 - prev_info["read_count"]) / (tm - prev_info["time"])
            io_stats["read_bytes"] = (io_counters.read_bytes * 1.0 - prev_info["read_bytes"]) / (tm - prev_info["time"])
            io_stats["write_count"] = (io_counters.write_count * 1.0 - prev_info["write_count"]) / (tm - prev_info["time"])
            io_stats["write_bytes"] = (io_counters.write_bytes * 1.0 - prev_info["write_bytes"]) / (tm - prev_info["time"])
            io_stats["write_chars"] = (io_counters.write_chars * 1.0 - prev_info["write_chars"]) / (tm - prev_info["time"])
            io_stats["read_chars"] = (io_counters.read_chars * 1.0 - prev_info["read_chars"]) / (tm - prev_info["time"])

        io_stats["read_count"] = io_counters.read_count * 1.0
        io_stats["read_bytes"] = io_counters.read_bytes * 1.0
        io_stats["write_count"] = io_counters.write_count * 1.0
        io_stats["write_bytes"] = io_counters.write_bytes * 1.0
        io_stats["read_chars"] = io_counters.read_chars * 1.0
        io_stats["write_chars"] = io_counters.write_chars * 1.0
        # else:
        #     io_stats["read_count"] = "0.0"
        #     io_stats["read_bytes"] = "0.0"
        #     io_stats["write_count"] = "0.0"
        #     io_stats["write_bytes"] = "0.0"

        return io_stats
            # storage = {}
        # of = self._p.open_files()
        # of = [f.__dict__ for f in of]
        # storage['open_files'] = of
        # storage['num_fds'] = self._p.num_fds()
        # storage['io_counters'] = self._p.io_counters().__dict__
        # return storage

    def _get_process_net(self):
        net = {}
        conns = self._p.connections()
        conns = [c.__dict__ for c in conns]
        net['connections'] = conns
        net['connections'] = []
        return net

    def _get_process_stats(self, tm, measurement):
        resources = {}
        cpu = self._get_process_cpu(tm, measurement)
        mem = self._get_process_mem()
        disk = self._get_process_storage(tm, measurement)
        # net = self._get_process_net()
        resources.update(cpu)
        resources.update(mem)
        resources.update(disk)
        # resources.update(net)
        return resources

    def options(self, **kwargs):
        options = self.serialize(**kwargs)
        self.cmd = self.monitor
        self.opts = options

    def get_pid(self, name):
        pidlist = []
        try:
            pidlist = list(map(int, check_output(["pidof", name]).split()))
        except  CalledProcessError:
            pidlist = []
        finally:
            if pidlist:
                pid = pidlist.pop()
            else:
                pid = None
            return pid

    def monitor(self, opts):
        metrics = []
        interval = 1
        pid = None

        if 'interval' in opts:
            interval = float(opts['interval'])

        if 'duration' in opts:
            t = float(opts.get('duration'))
        else:
            return metrics

        live = self.stimulus.get("live", False)
        url = self.stimulus.get("url", None)

        if 'pid' in opts:
            pid = int(opts['pid'])
        elif 'name' in opts:
            name = str(opts['name'])
            pid = self.get_pid(name)
        else:
            return metrics

        if not pid:
            logger.debug("pid not found")
            return metrics
        if not ps.pid_exists(pid):
            return metrics

        self._p = ps.Process(pid)
        stats = self._get_process_info()
        measurement = {}
        measurement["time"] = 0.0
        past = datetime.now()
        
        while True:
            current = datetime.now()
            seconds = (current-past).total_seconds()
            if seconds > t:
                break
            else:
                tm = time.time()
                measurement = self._get_process_stats(tm, measurement)
                measurement["time"] = tm
                # measurement.update(stats)
                self._first = False

                # _time = {'timestamp': current.strftime('%Y-%m-%dT%H:%M:%S.%fZ')}
                # measurement.update(_time)
        
                if live:
                    self.flush(url, measurement)

                metrics.append(measurement)
                time.sleep(interval)
        
        results = {
            "uuid": self.uuid,
            "metrics": metrics
        }
        return results

    def parser(self, output):
        metrics = []

        if output:
            out = output.get("metrics")
            metric_names = list(out[0].keys())
            
            for name in metric_names:
                # metric_values = dict([ (out.index(out_value),float(out_value.get(name))) for out_value in out ])
                metric_values = dict([ ( out.index(out_value), {"key":out.index(out_value), "value":float(out_value.get(name))} ) for out_value in out ])

                m = {
                    "name": name,
                    "type": "float",
                    "unit": "",
                    "series": metric_values,
                }

                metrics.append(m)
        
        self.metrics = metrics


class MonContainer(Tool):
    def __init__(self, url=None):
        Tool.__init__(self, 2, 'container')
        self._command = None
        self._connected_to_docker = False
        self.url = url
        if not url:
            self.url = 'unix://var/run/docker.sock'
        
    def cfg(self):
        params = {
            "interval": "interval",
            "target": "target",
            "duration": "duration",
        }
        self.parameters = params
        self.cmd = ""

    def connect(self):
        try:
            self._dc = docker.from_env()
            # self._dc = docker.APIClient(base_url='unix://var/run/docker.sock')
            # self._dc = docker.DockerClient(base_url=self.url)
            logger.info(self._dc.version())

        except Exception as e:
            self._dc = None
            logger.warn('could not connect to docker socket - check if docker is installed/running %s', e)
        else:
            self._connected_to_docker = True

    def _stats_cpu(self, stats):
        summary_stats_cpu = {}
        cpu_stats = stats['cpu_stats']
        cpu_usage = cpu_stats['cpu_usage']
        # summary_stats_cpu['cpu_throttling_data'] = cpu_stats['throttling_data']
        summary_stats_cpu['system_cpu_usage'] = cpu_stats['system_cpu_usage']
        summary_stats_cpu['cpu_total_usage'] = cpu_usage['total_usage'] 
        summary_stats_cpu['cpu_usage_in_kernelmode'] = cpu_usage['usage_in_kernelmode']
        summary_stats_cpu['cpu_usage_in_usermode'] = cpu_usage['usage_in_usermode']
        summary_stats_cpu['cpu_percent'] = self._stats_cpu_perc(stats)
        return summary_stats_cpu

    def _stats_cpu_perc(self, stats):
        cpu_stats = stats['cpu_stats']
        cpu_usage = cpu_stats['cpu_usage']
        system_cpu_usage = cpu_stats['system_cpu_usage']
        percpu = cpu_usage['percpu_usage']
        cpu_percent = 0.0
        if 'precpu_stats' in stats:
            precpu_stats = stats['precpu_stats']
            precpu_usage = precpu_stats['cpu_usage']
            cpu_delta = cpu_usage['total_usage'] - precpu_usage['total_usage']
            system_delta = system_cpu_usage - precpu_stats['system_cpu_usage']
            if system_delta > 0 and cpu_delta > 0:
                cpu_percent = 100.0 * cpu_delta / system_delta * len(percpu)
        return cpu_percent

    def _stats_mem(self, stats):
        summary_stats_mem = {}
        mem_stats = stats['memory_stats']
        
        in_mem_stats = mem_stats['stats']
        for k,v in in_mem_stats.items():
            new_k = 'mem_' + k
            summary_stats_mem[new_k] = v

        summary_stats_mem['mem_percent'] = self._stats_mem_perc(stats)
        summary_stats_mem['mem_limit'] = mem_stats['limit']
        summary_stats_mem['mem_max_usage'] = mem_stats['max_usage']
        summary_stats_mem['mem_usage'] = mem_stats['usage']
        return summary_stats_mem

    def _stats_mem_perc(self, stats):
        mem_stats = stats['memory_stats']
        mem_percent = 100.0 * mem_stats['usage'] / mem_stats['limit']
        return mem_percent

    def _stats_blkio(self, stats):
        blkio_values = {}
        blkio_stats = stats['blkio_stats']
        
        blkio_values['io_read'] = 0
        blkio_values['io_write'] = 0
        for key, values in blkio_stats.items():
            if key == 'io_service_bytes_recursive':
                for value in values:
                    if value['op'] == 'Read':
                        if value['value'] >= blkio_values['io_read']:
                            blkio_values['io_read'] = value['value']
                    if value['op'] == 'Write':
                        if value['value'] >= blkio_values['io_write']:
                            blkio_values['io_write'] = value['value']                    
        return blkio_values


    def _stats(self, name=None):
        summary_stats = {}
        
        container = self._dc.containers.get(name)
        if container:
            stats = container.stats(stream=False)
        else:
            return summary_stats
        
        stats_cpu = self._stats_cpu(stats)
        summary_stats.update(stats_cpu)
        stats_mem = self._stats_mem(stats)
        summary_stats.update(stats_mem)
        stats_io = self._stats_blkio(stats)
        summary_stats.update(stats_io)
        return summary_stats

    def options(self, **kwargs):
        options = self.serialize(**kwargs)
        self.cmd = self.monitor
        self.opts = options

    def monitor(self, opts):
        self.connect()

        metrics = []
        interval = 1
        t = 3

        if 'interval' in opts:
            interval = float(opts['interval'])
        if 'duration' in opts:
            t = float(opts['duration'])

        if 'target' in opts:
            name = opts['target']
        else:
            return metrics

        live = self.stimulus.get("live", False)
        url = self.stimulus.get("url", None)

        past = datetime.now()
        while True:
            current = datetime.now()
            _time = {'timestamp': current.strftime('%Y-%m-%dT%H:%M:%S.%fZ')}
            seconds = (current-past).total_seconds()
            if seconds > t:
                break
            else:
                measurement = self._stats(name=name)
                if 'read' in measurement:
                    del measurement['read']
                # measurement.update(_time)
                metrics.append(measurement)        

                if live:
                    self.flush(url, measurement)

                time.sleep(interval)

        results = {
            "uuid": self.uuid,
            "metrics": metrics
        }
        return results

    def parser(self, output):
        metrics = []

        if output:
            out = output.get("metrics")

            metric_names = list(out[0].keys())

            for name in metric_names:

                metric_values = dict([ ( out.index(out_value), {"key":out.index(out_value), "value":float(out_value.get(name))} )
                                    for out_value in out ])

                m = {
                    "name": name,
                    "type": "float",
                    "unit": "",
                    "series": metric_values,
                }

                metrics.append(m)
        
        results = {
            "uuid": self.uuid,
            "metrics": metrics
        }
        self.metrics = results
        

class MonHost(Tool):
    def __init__(self):
        Tool.__init__(self, 3, 'host')
        self._first = True
        self._command = None

    def cfg(self):
        params = {
            'interval':'interval',
            'duration':'duration',
        }
        self.parameters = params
        self.cmd = ""

    def _get_node_info(self):
        info = {}
        system, node, release, version, machine, processor = pl.uname()
        info['system'] = system
        info['node'] = node
        info['release'] = release
        info['version'] = version
        info['machine'] = machine
        info['processor'] = processor
        return info

    def _get_node_cpu(self, tm, prev_info):
        cpu_stats = {}
        cpu_stats["cpu_percent"] = ps.cpu_percent(interval=0.5)

        user, nice, system, idle, iowait, irq, softirq, steal, guest, guest_nice = ps.cpu_times()

        if self._first == False:
            cpu_stats["user_time"] = (user - prev_info["user_time"]) / (tm - prev_info["time"])
            cpu_stats["nice_time"] = (nice - prev_info["nice_time"]) / (tm - prev_info["time"])
            cpu_stats["system_time"] = (system - prev_info["system_time"]) / (tm - prev_info["time"])
            cpu_stats["idle_time"] = (idle - prev_info["idle_time"]) / (tm - prev_info["time"])
            cpu_stats["iowait_time"] = (iowait - prev_info["iowait_time"]) / (tm - prev_info["time"])
            cpu_stats["irq_time"] = (irq - prev_info["irq_time"]) / (tm - prev_info["time"])
            cpu_stats["softirq_time"] = (softirq - prev_info["softirq_time"]) / (tm - prev_info["time"])
            cpu_stats["steal_time"] = (steal - prev_info["steal_time"]) / (tm - prev_info["time"])
            cpu_stats["guest_time"] = (guest - prev_info["guest_time"]) / (tm - prev_info["time"])
            cpu_stats["guest_nice_time"] = (guest_nice - prev_info["guest_nice_time"]) / (tm - prev_info["time"])

        cpu_stats["user_time"] = user
        cpu_stats["nice_time"] = nice
        cpu_stats["system_time"] = system
        cpu_stats["idle_time"] = idle
        cpu_stats["iowait_time"] = iowait
        cpu_stats["irq_time"] = irq
        cpu_stats["softirq_time"] = softirq
        cpu_stats["steal_time"] = steal
        cpu_stats["guest_time"] = guest
        cpu_stats["guest_nice_time"] = guest_nice

        return cpu_stats
        # cpu = {}
        # cpu['logical'] = ps.cpu_count(logical=True)
        # cpu['cores'] = ps.cpu_count(logical=False)
        # cpu['cputimes'] = ps.cpu_times().__dict__
        # cpu['percent'] = ps.cpu_percent()
        # cpu['stats'] = ps.cpu_stats().__dict__
        # return cpu

    def _get_node_mem(self):
        mem_stats = {}

        vm = ps.virtual_memory()

        mem_stats["mem_percent"] = vm.percent

        mem_stats["total_mem"] = vm.total / (1024. * 1024.)
        mem_stats["available_mem"] = vm.available / (1024. * 1024.)
        mem_stats["used_mem"] = vm.used / (1024. * 1024.)
        mem_stats["free_mem"] = vm.free / (1024. * 1024.)
        mem_stats["active_mem"] = vm.active / (1024. * 1024.)
        mem_stats["inactive_mem"] = vm.inactive / (1024. * 1024.)
        mem_stats["buffers_mem"] = vm.buffers / (1024. * 1024.)
        mem_stats["cached_mem"] = vm.cached / (1024. * 1024.)
        mem_stats["shared_mem"] = vm.shared / (1024. * 1024.)
        mem_stats["slab_mem"] = vm.slab / (1024. * 1024.)

        return mem_stats
        # mem = {}
        # mem['virtual'] = ps.virtual_memory().__dict__
        # mem['swap'] = ps.swap_memory().__dict__
        # return mem

    def _get_node_storage(self, tm, prev_info):
        disk_stats = {}
        # read_count, write_count, read_bytes, write_bytes, read_time, write_time = ps.disk_io_counters()

        dio = ps.disk_io_counters()
        if self._first == False:
            disk_stats["read_count"] = (dio.read_count * 1.0 - prev_info["read_count"]) / (tm - prev_info["time"])
            disk_stats["read_bytes"] = (dio.read_bytes * 1.0 - prev_info["read_bytes"]) / (tm - prev_info["time"])
            disk_stats["write_count"] = (dio.write_count * 1.0 - prev_info["write_count"]) / (tm - prev_info["time"])
            disk_stats["write_bytes"] = (dio.write_bytes * 1.0 - prev_info["write_bytes"]) / (tm - prev_info["time"])

        disk_stats["read_count"] = dio.read_count * 1.0
        disk_stats["read_bytes"] = dio.read_bytes * 1.0
        disk_stats["write_count"] = dio.write_count * 1.0
        disk_stats["write_bytes"] = dio.write_bytes * 1.0

        return disk_stats
        # storage = {}
        # storage['partitions'] = {}
        # partitions = ps.disk_partitions()
        # for partition in partitions:
        #     partition_name,m,fst,o = partition
        #     storage['partitions'][partition_name] = ps.disk_usage(partition_name).total
        # storage['io_counters'] = ps.disk_io_counters(perdisk=False).__dict__
        # return storage

    def _get_node_net(self):
        net_stats = {}
        return net_stats
        # net = {}
        # stats = ps.net_if_stats()
        # counters = ps.net_io_counters(pernic=True)
        # for face in counters:
        #     counters[face] = counters[face].__dict__
        #     stats[face] = stats[face].__dict__
        # net['stats'] = stats
        # net['counters'] = counters
        # return net

    def _get_node_stats(self, tm, measurement):
        resources = {}
        cpu = self._get_node_cpu(tm, measurement)
        mem = self._get_node_mem()
        disk = self._get_node_storage(tm, measurement)
        net = self._get_node_net()
        resources.update(cpu)
        resources.update(mem)
        resources.update(disk)
        resources.update(net)
        return resources

    def options(self, **kwargs):
        options = self.serialize(**kwargs)
        self.cmd = self.monitor
        self.opts = options

    def monitor(self, opts):
        metrics = []
        interval = 1
        t = 3
        if 'interval' in opts:
            interval = float(opts.get('interval', 1))
        
        if 'duration' in opts:
            t = float(opts.get('duration', 0))
        else:
            return metrics

        live = self.stimulus.get("live", False)
        url = self.stimulus.get("url", None)

        past = datetime.now()
        # node_info = self._get_node_info()
        measurement = {}
        measurement["time"] = 0.0
        while True:
            current = datetime.now()
            _time = {'timestamp': current.strftime('%Y-%m-%dT%H:%M:%S.%fZ')}
            seconds = (current-past).total_seconds()
            if seconds > t:
                break
            else:
                tm = time.time()
                measurement = self._get_node_stats(tm, measurement)
                # measurement.update(node_info)
                measurement["time"] = tm
                current = datetime.now()
                self._first = False

                # measurement.update(_time)
                metrics.append(measurement)

                if live:
                    self.flush(url, measurement)

                time.sleep(interval)

        results = {
            "uuid": self.uuid,
            "metrics": metrics
        }
        return results

    def parser(self, output):
        metrics = []

        if output:
            out = output.get("metrics")
            metric_names = list(out[0].keys())

            for name in metric_names:
                # metric_values = dict([ (out.index(out_value),float(out_value.get(name))) for out_value in out ])

                metric_values = dict([ ( out.index(out_value), {"key":out.index(out_value), "value":float(out_value.get(name))} ) for out_value in out ])

                m = {
                    "name": name,
                    "type": "float",
                    "unit": "",
                    "series": metric_values,
                }

                metrics.append(m)
        
        self.metrics = metrics

class MonTcpdump(Tool):
    def __init__(self):
        Tool.__init__(self, 4, "tcpdump")
        self._output_folder = '/tmp/'

    def cfg(self):
        params = {
            'interface':'-i',
            'duration':'-G',
            'pcap':'-w'
        }
        self.parameters = params
        self.cmd = ""

    def options(self, **kwargs):
        options = self.serialize(**kwargs)
        
        if '-w' in options:
            pcap_value = options.get('-w')
            pcap_path = self.filepath(pcap_value)
            options['-w'] = pcap_path

        self.cmd = self.monitor
        self.opts = options
                
    def monitor(self, opts):
        args = ["tcpdump"]
        results = {
            "uuid": self.uuid,
            "metrics": {}
        }

        for k,v in opts.items():
            args.extend([k,v])

        timeout = opts.get("-G", None)
        if timeout:
            timeout = int(timeout)
        else:
            return results

        logger.info("MonTcpdump call %s", args)
        output_process = self.start_process(args, stop=True, timeout=timeout)
        logger.info("MonTcpdump output_process %s", output_process)

        pcap_file = opts.get("-w")
        metrics = self.parse_pcap(pcap_file)

        results = {
            "uuid": self.uuid,
            "metrics": metrics
        }
        return results

    def parse_pcap(self, pcap_file): #TODO
        return {"ack": pcap_file}

    def filepath(self, filename):
        _filepath = os.path.normpath(os.path.join(
            self._output_folder, filename))
        return _filepath

    def parse(self, out):
        self.metrics = out


class Tools:
    TOOLS = [
        MonProcess,
        MonContainer,
        MonHost,
        MonTcpdump,
        MonDummy,
    ]

    def __init__(self):
        self.toolset = {}
        self.load_tools()
        #ThreadPoolExecutor or ProcessPoolExecutor
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=4,
        )
    
    def load_tools(self):
        for tool_cls in self.TOOLS:
            tool_instance = tool_cls()
            tool_name = tool_instance.name
            self.toolset[tool_name] = tool_instance
        logger.debug("loaded toolset")

    def build_stimulus(self, ev, instruction):
        logger.debug("build stimulus from instruction")
        logger.debug(instruction)
        stimulus = {}

        for _id,args in instruction.items():
            tool_name = args.get("tool-name")
            tool_parameters = args.get("parameters")
            logger.debug(f"Stimulus set for tool-name {tool_name} - params {tool_parameters}")
            if tool_name in self.toolset:
                tool = self.toolset[tool_name]
                tool.init(ev, _id, args)
                stimulus[_id] = tool
                logger.debug("Stimulus set for tool-name %s", tool.name)
        return stimulus

    def outputs(self, results, stimulus, callback, ev):
        metrics = {}
        
        for result in results:
            _id = result.get("uuid")
            if _id in stimulus.keys():
                tool = stimulus.get(_id)
                tool_out = tool.outputs(result)
                metrics[_id] = tool_out

        data = {
            "type": "events",
            "event": "metrics",
            "group": "infrastructure",
            "metrics": metrics,
            "ev": ev,
        }
        logger.info(f"data: {data}")
        return data

    async def run(self, stimulus, callback, ev):
        logger.info('starting')
        logger.info('creating executor tasks')

        loop = asyncio.get_event_loop()

        blocking_tasks = [
            loop.run_in_executor(self.executor, tool.call(), tool.args())
            for tool in stimulus.values()
        ]

        logger.info('waiting for executor tasks')
        # completed, _ = await asyncio.wait(blocking_tasks)
        # results = [t.result() for t in completed]
        
        tasks = await asyncio.gather(*blocking_tasks, return_exceptions=True)

        results = []
        for aw in tasks:
            if isinstance(aw, Exception):
                logger.debug(f"Could not run _schedule task - exception {aw}")
            else:
                results.append(aw)
       
        logger.info('results: {!r}'.format(results))
        out = self.outputs(results, stimulus, callback, ev)
        return out

    async def workflow(self, data):
        instructions = data.get("instructions", None)
        callback = data.get("callback", None)
        ev = data.get("ev", None)

        tools = self.build_stimulus(ev, instructions)
        
        try:
            reply_output = await self.run(tools, callback, ev)
        except Exception as e:
            logger.info(f"Exception while running tools {e}")
            reply_output = {}
        finally:
            logger.info('Workflow exiting')
            return reply_output
            


    
if __name__ == '__main__':
    import sys 

    logging.basicConfig(
            level=logging.DEBUG,
            format='PID %(process)5s %(name)18s: %(message)s',
            stream=sys.stderr,
        )

    insts = {
        # 1: {
        #     "live": False,
        #     "url": "http://127.0.0.1:8989",
        #     "tool-name": "dummy",
        #     "parameters": {
        #         "duration": 3,
        #         "interval": 1,
        #     }
        # },
        # 2: {
        #     "live": False,
        #     "url": "http://127.0.0.1:8989",
        #     "tool-name": "process",
        #     "parameters": {
        #         "pid": 78083,
        #         "duration": 3,
        #         "interval": 1,
        #     }
        # },
        # 3: {
        #     "live": False,
        #     "url": "http://127.0.0.1:8989",
        #     "tool-name": "container",
        #     "parameters": {
        #         "target": "ivan",
        #         "duration": 3,
        #         "interval": 1,
        #     }
        # },
        # 4: {
        #     "live": False,
        #     "url": "http://127.0.0.1:8989",
        #     "tool-name": "host",
        #     "parameters": {
        #         "duration": 3,
        #         "interval": 1,
        #     }
        # },
        # 5: {
        #     "live": False,
        #     "url": "http://127.0.0.1:8989",
        #     "tool-name": "tcpdump",
        #     "parameters": {
        #         "duration": "3",
        #         "interface": "wlp2s0",
        #         "pcap": "mon-wlp2s0.pcap"
        #     }
        # }
    }

    data = {
        "callback": "http://127.0.0.1:8989",
        "instructions": insts,
    }
    
    tools = Tools()
    output = asyncio.run(tools.workflow(data))
    print(output)