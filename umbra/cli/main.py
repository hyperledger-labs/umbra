import os
import json
import asyncio
import logging

from umbra.design.configs import Scenario
from umbra.cli.envs import Environments
from umbra.cli.interfaces import BrokerInterface


logger = logging.getLogger(__name__)


class CLIRunner:
    def __init__(self):
        self.scenario = None
        self.topology = None
        self.scenario_config = {}
        self.environments = Environments()
        self.broker_interface = BrokerInterface()
        self.cmds = {
            "load": self.load,
            "start": self.start,
            "stop": self.stop,
            "install": self.install,
            "uninstall": self.uninstall,
            "begin": self.begin,
            "end": self.end,
        }

        self._status = {
            "load": False,
            "start": False,
            "stop": False,
            "install": False,
            "uninstall": False,
            "begin": False,
            "end": False,
        }
        logger.info("CLIRunner init")

    def get_cmds(self):
        return list(self.cmds.keys())

    def filepath(self, name):
        filepath = os.path.normpath(os.path.join(os.path.dirname(__file__), name))
        return filepath

    def load_file(self, filename):
        filepath = self.filepath(filename)
        data = {}
        error = ""
        try:
            with open(filepath, "+r") as fp:
                data = json.load(fp)
        except Exception as e:
            error = f"Load file error: {repr(e)}"
            logger.debug(error)
        else:
            logger.debug(f"Load file ok")
        finally:
            return data, error

    def load(self, filename):
        logger.info(f"Load triggered - filename {filename}")
        ack = True

        data, error = self.load_file(filename)

        if error:
            msg = "Config not loaded - " + error
        else:
            self.scenario = Scenario("")
            ack = self.scenario.parse(data)

            if ack:
                self.topology = self.scenario.get_topology()
                self.environments.generate_env_cfgs(self.topology)
                msg = "Config loaded"
            else:
                msg = "Config not loaded - Error parsing scenario data"

        self._status["load"] = ack
        logger.info(f"{msg}")
        return msg

    def start(self):
        logger.info(f"Start triggered")
        ack, messages = self.environments.implement_env_cfgs("start")
        self._status["start"] = ack

        logger.info(f"{messages}")
        return ack, messages

    def stop(self):
        logger.info(f"Stop triggered")
        ack, messages = self.environments.implement_env_cfgs("stop")
        self._status["start"] = not ack
        self._status["stop"] = ack

        logger.info(f"{messages}")
        return messages

    def install(self):
        logger.info(f"install triggered")
        ack, messages = self.environments.implement_env_cfgs("install")
        self._status["install"] = ack

        logger.info(f"{messages}")
        return ack, messages

    def uninstall(self):
        logger.info(f"uninstall triggered")
        ack, messages = self.environments.implement_env_cfgs("uninstall")
        self._status["install"] = not ack
        self._status["uninstall"] = ack

        logger.info(f"{messages}")
        return messages

    def begin(self):
        logger.info(f"begin triggered")
        default_env = self.topology.get_default_environment()
        default_env_components = default_env.get("components")
        broker_env = default_env_components.get("broker")

        scenario = self.scenario.dump()
        reply, error = self.broker_interface.begin(broker_env, scenario)

        ack = False if error else True
        self._status["begin"] = ack

        if ack:
            messages = reply
        else:
            messages = error

        logger.info(f"{messages}")
        return ack, messages

    def end(self):
        logger.info(f"end triggered")
        default_env = self.topology.get_default_environment()
        default_env_components = default_env.get("components")
        broker_env = default_env_components.get("broker")

        scenario = self.scenario.dump()
        reply, error = self.broker_interface.end(broker_env, scenario)

        ack = False if error else True
        self._status["end"] = ack
        self._status["begin"] = not ack

        if ack:
            messages = reply
        else:
            messages = error

        logger.info(f"{messages}")
        return ack, messages

    def status(self, command):
        ack = False
        error = ""

        if command == "load":
            ack = not self._status["start"]
            if not ack:
                error = "Cannot load - config started - stop it first"

        if command == "start":
            ack = self._status["load"] and not self._status["start"]
            if not ack:
                error = "Cannot start - config not loaded or config started"

        if command == "stop":
            ack = self._status["start"] and not self._status["stop"]
            if not ack:
                error = "Cannot stop - config not started or config stopped"

        if command == "install":
            pass

        if command == "uninstall":
            pass

        if command == "begin":
            pass

        if command == "end":
            pass

        return True, error

    def execute(self, cmds):
        cmd = cmds[0]
        logger.info(f"Executing commands: {cmds}")

        ok, error = self.status(cmd)

        if ok:
            available_cmds = list(self.cmds.keys())

            if cmd == "load":
                if len(cmds) == 2:
                    config_filename = cmds[1]
                    output = self.load(config_filename)
                    return output
                else:
                    return "Missing config filepath"

            if cmd in available_cmds:
                func = self.cmds.get(cmd)
                output = func()
                return output

            else:
                output = f"Command not found in {available_cmds}"
                return output

        else:
            return error


class CLI:
    def __init__(self):
        self.runner = CLIRunner()
        self._runner_cmds = self.runner.get_cmds()

    def validator(self, text):
        words = text.split()

        if words:
            cmd = words[0]

            if cmd in self._runner_cmds:
                return words
            else:
                print(
                    f"Error: command {cmd} not available in commands {self._runner_cmds}"
                )

        return []

    def print_output(self, output):
        if type(output) is str:
            print(output)
        elif type(output) is list:
            for out in output:
                print(out)
        else:
            print(f"Unkown command output format {type(output)}")

    def init(self, session):
        logger.info("CLI init")
        while True:
            try:
                text = session.prompt("umbra> ")
            except KeyboardInterrupt:
                continue
            except EOFError:
                break

            try:
                commands = self.validator(text)
            except Exception as e:
                print(repr(e))
            else:

                if commands:
                    output = self.runner.execute(commands)
                    self.print_output(output)

        print("GoodBye!")
