import os
import json
import asyncio
import logging

from prompt_toolkit.shortcuts import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

from umbra.design.configs import Experiment
from umbra.cli.envs import Environments
from umbra.cli.interfaces import BrokerInterface
from umbra.cli.output import print_cli, format_text


logger = logging.getLogger(__name__)


class CLIRunner:
    def __init__(self):
        self.experiment = None
        self.topology = None
        self.experiment_config = {}
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

        print_cli(f"Loading configuration file at {filename}")

        data, error = self.load_file(filename)

        if error:
            msg = "Configuration not loaded - " + error
            print_cli(None, err=msg, style="error")
        else:
            self.experiment = Experiment("")
            ack = self.experiment.parse(data)

            if ack:
                self.topology = self.experiment.get_topology()
                self.environments.generate_env_cfgs(self.topology)
                msg = "Configuration loaded"
                print_cli(msg, style="normal")
            else:
                msg = "Configuration not loaded - Error parsing scenario data"
                print_cli(None, err=msg, style="error")

        self._status["load"] = ack

        logger.info(f"{msg}")
        return msg

    async def start(self):
        logger.info(f"Start triggered")

        print_cli(f"Starting", style="attention")

        ack, messages = self.environments.implement_env_cfgs("start")
        self._status["start"] = ack

        logger.info(f"{messages}")
        return ack, messages

    async def stop(self):
        logger.info(f"Stop triggered")

        print_cli(f"Stopping", style="attention")

        ack, messages = self.environments.implement_env_cfgs("stop")
        self._status["start"] = not ack
        self._status["stop"] = ack

        logger.info(f"{messages}")
        return messages

    async def install(self):
        logger.info(f"install triggered")

        print_cli(f"Installing", style="attention")

        ack, messages = self.environments.implement_env_cfgs("install")
        self._status["install"] = ack

        logger.info(f"{messages}")
        return ack, messages

    async def uninstall(self):
        logger.info(f"uninstall triggered")

        print_cli(f"Uninstalling", style="attention")

        ack, messages = self.environments.implement_env_cfgs("uninstall")
        self._status["install"] = not ack
        self._status["uninstall"] = ack

        logger.info(f"{messages}")
        return messages

    async def begin(self):
        logger.info(f"begin triggered")

        print_cli(f"Beginning", style="attention")

        default_env = self.topology.get_default_environment()
        default_env_components = default_env.get("components")
        broker_env = default_env_components.get("broker")

        print_cli(f"Experiment Begin", style="info")
        scenario = self.experiment.dump()
        reply, error = await self.broker_interface.begin(broker_env, scenario)

        ack = False if error else True
        self._status["begin"] = ack

        if ack:
            print_cli(f"Umbra Experiment Ok", style="normal")
            messages = reply
        else:
            print_cli(f"Umbra Experiment Error", style="error")
            messages = error

        logger.info(f"{messages}")
        return ack, messages

    async def end(self):
        logger.info(f"end triggered")

        print_cli(f"Ending", style="attention")

        default_env = self.topology.get_default_environment()
        default_env_components = default_env.get("components")
        broker_env = default_env_components.get("broker")

        print_cli(f"Experiment End", style="info")
        scenario = self.experiment.dump()
        reply, error = await self.broker_interface.end(broker_env, scenario)

        ack = False if error else True
        self._status["end"] = ack
        self._status["begin"] = not ack

        if ack:
            print_cli(f"Ended Umbra Experiment", style="normal")
            messages = reply
        else:
            print_cli(f"Ended Umbra Experiment Error", style="error")
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

    async def execute(self, cmds):
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
                output = await func()
                return output

            else:
                output = f"Command not found in {available_cmds}"
                return output

        else:
            return error


class CLI:
    umbra_completer = WordCompleter(
        ["load", "start", "stop", "install", "uninstall", "begin", "end"],
        ignore_case=True,
    )

    umbra_style = Style.from_dict(
        {
            "completion-menu.completion": "bg:#008888 #ffffff",
            "completion-menu.completion.current": "bg:#00aaaa #000000",
            "scrollbar.background": "bg:#88aaaa",
            "scrollbar.button": "bg:#222222",
            "main": "#fb5607",
            "normal": "#ffd500",
            "error": "#d7263d",
            "info": "#3a86ff",
            "attention": "#8338ec",
            "warning": "#ff006e italic",
            "prompt": "#00bbf9 bold",
        }
    )

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
            print_cli(output, style="normal")
        elif type(output) is list:
            for out in output:
                print_cli(out, style="normal")
        else:
            print_cli(f"Unkown command output format {type(output)}", style="attention")

    async def init(self):
        logger.info("CLI init")

        session = PromptSession(
            complete_while_typing=True,
            completer=CLI.umbra_completer,
            style=CLI.umbra_style,
            auto_suggest=AutoSuggestFromHistory(),
        )

        prompt = ":umbra> "

        try:
            while True:
                try:
                    prompt_text = format_text(prompt, style="prompt")
                    text = await session.prompt_async(prompt_text)

                except KeyboardInterrupt:
                    continue
                except EOFError:
                    break

                try:
                    commands = self.validator(text)
                except Exception as e:
                    logger.debug(repr(e))
                else:

                    if commands:
                        await self.runner.execute(commands)
                        # ack, reply = await self.runner.execute(commands)

        finally:
            logger.debug("GoodBye!")
