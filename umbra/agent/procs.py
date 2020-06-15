import logging
import subprocess
import time
from multiprocessing import Process, Queue

logger = logging.getLogger(__name__)


class Processors:
    def __init__(self):
        self.process = None

    def start_process(self, args, queue, stop=False, timeout=60):
        return_code = 0
        out, err = '', None
        try:
            p = subprocess.Popen(args,
                stdin = subprocess.PIPE,
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE,
                )
            self.process = p
            # logger.debug('process started %s', p.pid)
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
        except OSError:
            return_code = -1
            err = 'ERROR: exception OSError'
        finally:
            # logger.debug('process stopped')
            if return_code != 0:
                queue_answer = err
            else:
                queue_answer = out
            self.process = None
            queue.put(return_code)
            queue.put(queue_answer)
            queue.put('STOP')
            queue.close()
            return return_code

    def stop_process(self, timeout):
        if self.process:
            time.sleep(timeout)
            self.process.kill()
            # logger.info('process stopped %s', self.process.pid)
            self.process = None
            return True
        return False


class Multiprocessor:
    def __init__(self):
        self.processes = {}
        self.processor = Processors()

    def make_process(self, cmd, stop, timeout):
        q = Queue()
        p = Process(target=self.processor.start_process, args=(cmd, q, stop, timeout))
        return (p,q)

    def start_processes(self, stms):
        # logger.debug('start_processes')
        self.processes = {}
        for _id,stm in stms.items():
            cmd = stm.get("cmd")
            stop = stm.get("stop") 
            timeout = stm.get("timeout")
            self.processes[_id] = self.make_process(cmd, stop, timeout)
        # logger.debug('processes %s', self.processes)
        for (p,q) in self.processes.values():
            p.start()

    def check_processes(self):
        any_alive = True
        while any_alive:
            any_alive = any([p.is_alive() for (p,q) in self.processes.values()])
            all_queued = all([not q.empty() for (p, q) in self.processes.values()])
            time.sleep(0.05)
            if all_queued and any_alive:
                break
        return True

    def dump_queues(self, queue):
        return_code = queue.get()
        result = ""
        for i in iter(queue.get, 'STOP'):
            if type(i) is str:
                str_frmtd = i
            else:
                str_frmtd = i.decode("utf-8") 
            result += str_frmtd
        return return_code,result

    def get_processes_queue(self):
        outs = {}
        for _id, (p, q) in self.processes.items():
            exitcode, _res = self.dump_queues(q)
            p.terminate()
            outs[_id] = (exitcode, _res)
        return outs

    def run(self, stimulus):
        self.start_processes(stimulus)
        _outputs = {}
        if self.check_processes():
            _outputs = self.get_processes_queue()
        return _outputs


class Runner:
    def __init__(self):
        self._multi_processor = Multiprocessor()
        self._exe = {'py': '/usr/bin/python3',
                     'sh': 'sh',
                     'pl': 'perl',
                     'java': 'java'}

    def _parse_cmd(self, cmd):
        if type(cmd) is list:
            cmd = [str(c) for c in cmd]
        else:
            cmd = cmd.split(' ')
        return cmd

    def _parse_type(self, cmd):
        type = 'sh'
        _cmd = self._parse_cmd(cmd)
        _cmd = _cmd[0]
        if len(_cmd.split('.')) > 1:
            if _cmd.split('.')[-1] in self._exe:
                type = self._exe[_cmd.split('.')[-1]]
            else:
                type = None
        else:
            type = None
        return type

    def _cmd_exec_local(self, cmd):
        # logger.debug('_exec_local')
        _type = self._parse_type(cmd)
        if type(cmd) is list:
            cmd = [str(c) for c in cmd]
            cmd = ' '.join(cmd)
        if _type:
            cmd = _type + ' ' + cmd
        cmd = self._parse_cmd(cmd)
        logger.debug(cmd)
        return cmd

    def _output(self, ret, out):
        if ret == 0:
            return 'ok',out
        else:
            return None,out

    def _build_cmd(self, stms):
        built_cmds = {}
        for _id, stm in stms.items():
            cmd = stm.get("cmd")
            _cmd = self._cmd_exec_local(cmd)
            built_cmds[_id] = {
                'cmd':_cmd,
                'stop': stm.get("stop"),
                'timeout': stm.get("timeout"),
            }
        return built_cmds

    def _parse_outputs(self, outputs):
        parsed_outs = {}
        for _id,output in outputs.items():
            (ret, out) = output
            # logger.debug('ret %s, output %s', ret, out)
            parsed_outs[_id] = self._output(ret, out)
        return parsed_outs

    def run(self, stms):
        cmds = self._build_cmd(stms)
        outputs = self._multi_processor.run(cmds)
        outs = self._parse_outputs(outputs)
        return outs


if __name__ == "__main__":
    # m = Multiprocessor()
    # cmds = [["ping", "-c", "10", "8.8.8.8"], ["ping", "-c", "20", "8.8.8.8"]]
    # outputs = m.run(cmds)
    # print outputs

    runner = Runner()
    # cmd = "ping -c 3 8.8.8.8"
    cmds = {1:["ping", "-c", "2", "8.8.8.8"], 2:["ping", "-c", "1", "8.8.8.8"]}
    # path = '/home/erapvic/gits/vbaas/Codes/taas/taas/core/agent/probers/python2.7/prober_ping.py --info a'
    # path = {1:['python3', '/home/erapvic/gits/intrig/taas/taas/core/monitor/listeners/listener_host.py', '--duration', '20', '--interval', '1']}
    path = {1:['/usr/bin/python3', '/home/raphael/git/playground/gym/gym/common/profiler/info/info_environment.py']}
    outs = runner.run(path)
    # outs = runner.run(cmds, parallel=True)
    # outs = runner.run(cmds, parallel=True, remote=True, host="127.0.0.1", user='root')
    for _id,(ack, msg) in outs.items():
        print(_id,ack)
        print(msg)
