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
        }

        self._status = {
            "load": False,
            "start": False,
            "stop": False,
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
        try:
            with open(filepath, "+r") as fp:
                data = json.load(fp)
        except Exception as e:
            logger.debug(f"Load file error: {e}")
        else:
            logger.debug(f"Load file ok")
        finally:
            return data

    def load(self, filename):
        logger.info(f"Load triggered - filename {filename}")
        ack = True

        scenario_config = self.load_file(filename)
        if scenario_config:
            self.scenario = Scenario("")
            self.scenario.parse(scenario_config)
            self.topology = self.scenario.get_topology()
            self.environments.generate_env_cfgs(self.topology)
        else:
            ack = False

        if ack:
            msg = "Config loaded"
        else:
            msg = "Config not loaded"

        self._status["load"] = ack
        logger.info(f"{msg}")
        return msg

    def start(self):
        logger.info(f"Start triggered")
        ack = self.environments.implement_env_cfgs("start")
        self._status["start"] = ack

        if ack:
            msg = "Topology started"
        else:
            msg = "Topology not started"

        logger.info(f"{msg}")
        return msg

    def stop(self):
        logger.info(f"Stop triggered")
        ack = self.environments.implement_env_cfgs("stop")
        self._status["start"] = not ack
        self._status["stop"] = ack

        if ack:
            msg = "Topology stopped"
        else:
            msg = "Topology not stopped"

        logger.info(f"{msg}")
        return msg

    def status(self, command):
        ack = False

        if command == "load":
            ack = not self._status["start"]
            error = "Cannot load config - config started - stop it first"

        if command == "start":
            ack = self._status["load"] and not self._status["start"]
            error = "Cannot start config - config not loaded or config started"

        if command == "stop":
            ack = self._status["start"] and not self._status["stop"]
            error = "Cannot stop config - config not started or config stopped"

        return ack, error

    def execute(self, cmds):
        cmd = cmds[0]

        ok, error = self.status(cmd)

        if ok:

            if cmd == "load":
                if len(cmds) == 2:
                    config_filename = cmds[1]
                    output = self.load(config_filename)
                    return output
                else:
                    return "Missing config filepath"

            if cmd == "start":
                func = self.cmds.get(cmd)
                output = func()
                return output

            if cmd == "stop":
                func = self.cmds.get(cmd)
                output = func()
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
                    print(output)

        print("GoodBye!")
