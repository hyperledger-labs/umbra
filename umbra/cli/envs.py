import os
import json
import logging
import paramiko
import traceback
import asyncio
import subprocess
from scp import SCPClient, SCPException

from umbra.cli.output import print_cli


logger = logging.getLogger(__name__)


class RemotePlugin:
    def __init__(self):
        self._cfg = None
        self._client = None

    def cfg(self, cfg):
        logger.debug(f"ProxyPlugin cfg set: {cfg}")
        self._cfg = cfg

    def _connect(self):
        connect_flag = True
        try:
            self._client = paramiko.SSHClient()
            # self._client.load_system_host_keys()
            self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            self._client.connect(
                hostname=self._cfg.get("address"),
                port=self._cfg.get("port"),
                username=self._cfg.get("user"),
                password=self._cfg.get("password"),
                look_for_keys=False,
                timeout=60,
            )

        except Exception as e:
            logger.debug(f"ssh connect exception: {e.__class__}, {e}")
            traceback.print_exc()

            try:
                self._client.close()
            except:
                pass
            finally:
                connect_flag = False
                self._client = None

        finally:
            return connect_flag

    def execute_command(self, command, daemon=False):
        """Execute a command on the remote host."""

        self.ssh_output = None
        result_flag = True
        result = ""

        try:
            if self._connect():
                logger.info("Executing remote command --> {}".format(command))
                _, stdout, stderr = self._client.exec_command(command, timeout=None)

                if daemon:
                    stdout.channel.close()
                    stderr.channel.close()

                self.ssh_output = stdout.read()
                self.ssh_error = stderr.read()

                if self.ssh_error:
                    logger.info(
                        f"Problem occurred while running command: error {self.ssh_error}"
                    )
                    # result_flag = False
                    result = str(self.ssh_error) if self.ssh_error else "error"

                if self.ssh_output:
                    logger.info(
                        f"Command execution completed successfully: output {self.ssh_output}"
                    )
                    result = str(self.ssh_output) if self.ssh_output else "ok"

                self._client.close()
            else:
                print("Could not establish SSH connection")
                result_flag = False

        except paramiko.SSHException:
            logger.info(f"Failed to execute the commands {command}")
            self._client.close()
            result_flag = False

        return result_flag, result

    def copy_files(self, local_filepath, remote_filepath):
        """This method uploads a local file to a remote server"""
        logger.info(f"Remote-Copying files from {local_filepath} to {remote_filepath}")

        result_flag = True
        if self._connect():
            try:

                self.scp = SCPClient(self._client.get_transport())

                self.scp.put(
                    local_filepath, recursive=True, remote_path=remote_filepath
                )

                self._client.close()
                logger.info("Files successfully copied to remote host")

            except Exception as e:
                logger.info(
                    f"Unable to upload the file {local_filepath}"
                    f" to the remote server - exception {e}"
                )

                result_flag = False
                self._client.close()
        else:
            logger.info("Could not establish SSH connection")
            result_flag = False

        return result_flag


class LocalPlugin:
    def execute_command(self, args, daemon=False):
        """Run a process using the provided args
        if stop is true it waits the timeout specified
        before stopping the process, otherwise waits till
        the process stops

        Arguments:
            args {list} -- A process command to be called

        Keyword Arguments:
            stop {boll} -- If the process needs to be stopped (true)
            or will stop by itself (false) (default: {False})
            timeout {int} -- The time in seconds to wait before
            stopping the process, in case stop is true (default: {60})

        Returns:
            tuple -- (int, string, string) The return code of the
            process, its stdout and its stderr (both formated in json)
        """
        code, out, err = 0, {}, {}

        try:
            logger.info(f"Running local process {args}")
            result = subprocess.run(
                args,
                check=True,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logger.info(f"Process Status {result}")
            code = result.returncode
            out = result.stdout
            err = result.stderr

        except Exception as e:
            logger.info(f"Process exception {repr(e)}")
            code = -1
            err = repr(e)
        finally:
            if code == 0:
                out_str = str(out) if out else "ok"
                logger.info(f"Process stdout {out_str}")
                return True, out_str
            else:
                err_str = str(err) if err else "error"
                logger.info(f"Process stderr {err_str}")
                return False, err_str

    def copy_files(self, source, destination):
        logger.info(f"Local-Copying files from {source} to {destination}")
        return True


class Proxy:
    def __init__(self):
        self._remote_plugin = RemotePlugin()
        self._local_plugin = LocalPlugin()
        self._plugin = None
        self.model = ""
        self.envid = None
        self.host_cfg = {}
        self.components = {}
        self.settings = {}
        self._envs_stats = {}

    def clear(self):
        self._plugin = None
        self.model = ""
        self.host_cfg = {}
        self.components = {}
        self.settings = {}
        self._envs_stats = {}

    def load(self, env_cfg):
        logger.info(f"Loading environment config")
        self.remote = env_cfg.get("remote", False)
        self.envid = env_cfg.get("id")

        if self.remote:
            self.host_cfg = env_cfg.get("host")
            self._remote_plugin.cfg(self.host_cfg)
            self._plugin = self._remote_plugin
        else:
            self._plugin = self._local_plugin

        self.components = env_cfg.get("components")
        self.settings = env_cfg.get("settings")
        self.model = env_cfg.get("model")

        self._envs_stats[self.envid] = {
            "components": {},
        }

        logger.info(
            f"Environment: id {env_cfg.get('id')}, model {env_cfg.get('model')}, remote {env_cfg.get('remote')}"
        )
        logger.info(f"Components: {env_cfg.get('components')}")

    def _workflow_monitor(self, action):
        logger.info(f"Workflow monitor {action}")

        self._workflow_source_files("install")

        if action == "start":
            cmd = "cd /tmp/umbra/source && sudo make start-aux-monitor"
        elif action == "stop":
            cmd = "cd /tmp/umbra/source && sudo make stop-aux-monitor"
        else:
            cmd = None

        if cmd:
            ack, msg = self._plugin.execute_command(cmd)
            logger.info(f"Workflow {action}: monitor aux component {ack} - {msg}")

    def _workflow_start(self, name, info):
        logger.info(f"Workflow start: component {name}")

        if self.envid == "umbra-default" and name == "broker":
            self._workflow_monitor(action="start")

        cmd = "sudo umbra-{name} --uuid {uuid} --address {address} --debug &".format(
            name=name, uuid=info.get("uuid"), address=info.get("address")
        )
        ack, msg = self._plugin.execute_command(cmd, daemon=True)

        output = {
            "ack": ack,
            "msg": [msg],
        }
        logger.info(f"Stats: {ack} - msg: {msg}")
        return output

    def _workflow_stop(self, name, info):
        logger.info(f"Workflow stop: component {name}")

        cmd = "sudo pkill -9 'umbra-{name}'".format(name=name)
        ack, msg = self._plugin.execute_command(cmd)

        output = {
            "ack": ack,
            "msg": [msg],
        }
        logger.info(f"Stats: {ack} - msg: {msg}")

        if self.envid == "umbra-default" and name == "broker":
            self._workflow_monitor(action="stop")

        return output

    def _workflow_model(self, action):
        logger.info(f"Workflow model {self.model} - action {action}")
        action_cmd = f"cd /tmp/umbra/source && sudo make {action}-{self.model}"
        ack_action, msg_action = self._plugin.execute_command(action_cmd)
        logger.info(f"Stats: {ack_action} - msg: {msg_action}")
        return ack_action, msg_action

    def _workflow_source_hasfiles(self):
        for dirpath, dirnames, files in os.walk("/tmp/umbra/source"):
            if files:
                logger.info(f"Source files - {dirpath} has files: {dirnames}")
                return True
            if not files:
                logger.info(f"Source files - {dirpath} is empty: {dirnames}")
                return False
            break

    def _workflow_source_files(self, action):
        logger.info(f"Workflow source files - action {action}")
        ack_source_files, msg_source_files = True, ""

        if action == "install":
            # self._workflow_source_files("uninstall")
            clone_cmd = (
                "git clone https://github.com/raphaelvrosa/umbra /tmp/umbra/source"
            )

            if self._workflow_source_hasfiles():
                logger.info(f"Umbra source files already cloned to: /tmp/umbra/source")
            else:
                ack_source_files, msg_source_files = self._plugin.execute_command(
                    clone_cmd
                )

        if action == "uninstall":
            rm_cmd = "sudo rm -R /tmp/umbra/source"
            ack_source_files, msg_source_files = self._plugin.execute_command(rm_cmd)

        return ack_source_files, msg_source_files

    def _workflow_install(self):
        logger.info(f"Workflow install")

        source = self.settings.get("source")
        destination = self.settings.get("destination")

        if self.remote:
            create_dir_cmd = f"mkdir -p {destination}"
            ack_create_dir_cmd, msg_create_dir_cmd = self._plugin.execute_command(
                create_dir_cmd
            )
            logger.info(
                f"Creating remote dir - {ack_create_dir_cmd} - {msg_create_dir_cmd}"
            )

        ack = self._plugin.copy_files(source, destination)

        if ack:
            ack_clone, msg_clone = self._workflow_source_files("install")
            logger.info("Executing command - install requirements, deps, umbra install")
            install_cmd = "cd /tmp/umbra/source && sudo apt install -y make && sudo make requirements install-deps install"
            ack_install, msg_install = self._plugin.execute_command(install_cmd)

            ack_install_model, msg_install_model = self._workflow_model("install")

            ack = ack_clone and ack_install and ack_install_model
            msg = [
                "clone: " + msg_clone,
                "install: " + msg_install,
                "install-model :" + msg_install_model,
            ]
            output = {
                "ack": ack,
                "msg": msg,
            }

        else:
            output = {
                "ack": ack,
                "msg": "Could not upload configuration files to remote",
            }
        return output

    def _workflow_uninstall(self):
        logger.info(f"Workflow uninstall")

        ack_uninstall_model, msg_uninstall_model = self._workflow_model("uninstall")

        logger.info(f"Executing command - uninstall umbra")
        uninstall_cmd = "cd /tmp/umbra/source  && sudo make uninstall uninstall-deps"
        ack_uninstall, msg_uninstall = self._plugin.execute_command(uninstall_cmd)

        ack_rm, msg_rm = self._workflow_source_files("uninstall")

        ack = ack_rm and ack_uninstall and ack_uninstall_model
        msg = [
            "remove: " + msg_rm,
            "uninstall: " + msg_uninstall,
            "uninstall-model: " + msg_uninstall_model,
        ]
        output = {
            "ack": ack,
            "msg": msg,
        }
        return output

    def implement(self, actions):
        """Realizes the instantiation of the environment configuration

        Args:
            env_cfg (dict): The description of the environment configuration
            to be implemented, example:

            env_cfg = {
                "id": "X",
                "host": {
                    "user": "umbra",
                    "address": "192.168.122.156",
                    "port": "22",
                    "password": "123",
                }
                "settings": {
                    "source": "/tmp/umbra/...",
                    "destination": "/tmp/umbra/...",
                },
                "components": {
                    "scenario": {
                        "uuid": "y",
                        "address": "0.0.0.0:8988",
                    },
                    "broker": {},
                    "monitor": {}
                }
            }

        Returns:
            bool: If the transaction was successful (True) or not (False)
        """
        logger.info(f"Implementing actions - {actions} ")

        action_outputs = {}

        for action in actions:
            action_output = {}

            if action in ["install"]:
                logger.info(f"Implementing action - {action}")

                is_installed = self._envs_stats[self.envid].get(action, False)

                if not is_installed:
                    logger.info(
                        f"Calling action - {action} - Installing environment {self.envid}"
                    )

                    print_cli(f"Installing Umbra at environment {self.envid}")

                    action_output = self._workflow_install()
                    self._envs_stats[self.envid][action] = action_output.get("ack")

                    if action_output.get("ack"):
                        print_cli(
                            f"Install Umbra in environment {self.envid} Ok",
                            style="normal",
                        )

                    else:
                        print_cli(
                            f"Install Umbra in environment {self.envid} Error",
                            style="error",
                        )

                else:
                    logger.info(
                        f"Calling action {action} not needed - environment already installed"
                    )

                    print_cli(
                        f"Installing Umbra in environment {self.envid} not needed - environment already installed",
                        style="attention",
                    )

                    action_output = {
                        "ack": True,
                        "msg": ["install: environment already installed"],
                    }

            if action in ["uninstall"]:
                is_installed = self._envs_stats[self.envid].get(action, False)

                if is_installed:
                    logger.info(
                        f"Calling action - {action} - Uninstalling environment {self.envid}"
                    )

                    print_cli(f"Uninstalling Umbra at environment {self.envid}")

                    action_output = self._workflow_uninstall()
                    self._envs_stats[self.envid][action] = action_output.get("ack")

                    if action_output.get("ack"):
                        print_cli(
                            f"Uninstall Umbra in environment {self.envid} Ok",
                            style="normal",
                        )

                    else:
                        print_cli(
                            f"Uninstall Umbra in environment {self.envid} Error",
                            style="error",
                        )

                else:
                    logger.info(
                        f"Calling action {action} not needed - environment not installed"
                    )
                    print_cli(
                        f"Uninstalling Umbra in environment {self.envid} not needed - environment not installed",
                        style="attention",
                    )

                    action_output = {
                        "ack": False,
                        "msg": ["uninstall: environment not installed"],
                    }

            if action in ["start"]:
                for name, info in self.components.items():
                    logger.info(
                        f"Calling action {action} - environment {self.envid} - component {name}"
                    )

                    print_cli(
                        f"Starting component 'umbra-{name}' in environment {self.envid}"
                    )

                    action_output = self._workflow_start(name, info)

                    self._envs_stats[self.envid]["components"].setdefault(name, {})
                    self._envs_stats[self.envid]["components"][name].setdefault(
                        action, False
                    )

                    self._envs_stats[self.envid]["components"][name][
                        action
                    ] = action_output.get("ack")

                    if action_output.get("ack"):
                        print_cli(
                            f"Started component 'umbra-{name}' in environment {self.envid} Ok",
                            style="normal",
                        )

                    else:

                        print_cli(
                            f"Started component 'umbra-{name}' in environment {self.envid} Error",
                            style="error",
                        )

            if action in ["stop"]:
                for name, info in self.components.items():
                    logger.info(
                        f"Calling action {action} - environment {self.envid} - component {name}"
                    )

                    print_cli(
                        f"Stopping component 'umbra-{name}' in environment {self.envid}"
                    )

                    action_output = self._workflow_stop(name, info)

                    self._envs_stats[self.envid]["components"].setdefault(name, {})
                    self._envs_stats[self.envid]["components"][name].setdefault(
                        action, False
                    )
                    self._envs_stats[self.envid]["components"][name][
                        action
                    ] = action_output.get("ack")

                    if action_output.get("ack"):
                        print_cli(
                            f"Stopped component 'umbra-{name}' in environment {self.envid} Ok",
                            style="normal",
                        )

                    else:

                        print_cli(
                            f"Stopped component 'umbra-{name}' in environment {self.envid} Error",
                            style="error",
                        )

            if action_output:
                action_outputs[action] = action_output

        all_acks = all(
            [
                action_output.get("ack", False)
                for action_output in action_outputs.values()
            ]
        )

        return all_acks, action_outputs


class Environments:
    def __init__(self):
        self._proxy = Proxy()
        self.env_cfgs = {}
        self.env_stats = {}

    def generate_env_cfgs(self, topology):
        logger.info("Generating environments configuration")
        self._proxy.clear()
        envs = topology.get_environments()
        setts = topology.get_settings()
        model = topology.get_model()

        env_cfgs = {}

        for envid, env in envs.items():

            src_folder = setts
            dst_folder = setts.split("/")
            dst_folder = "/".join(dst_folder[:-1])

            logger.info(f"Settings: src_folder {src_folder} - dst_folder {dst_folder}")

            env_cfg = {
                "id": envid,
                "model": model,
                "remote": env.get("remote", False),
                "settings": {
                    "source": src_folder,
                    "destination": dst_folder,
                },
                "components": env.get("components"),
                "host": env.get("host", {}),
            }

            env_cfgs[envid] = env_cfg

        self.env_cfgs = env_cfgs

    def augment_action(self, action, revert=False):
        actions = []

        if action == "start":
            if revert:
                actions.extend(["stop"])
            else:
                actions.extend(["start"])

        if action == "stop":
            if revert:
                actions.extend(["start"])
            else:
                actions.extend(["stop"])

        if action == "install":
            if revert:
                actions.extend(["uninstall"])
            else:
                actions.extend(["install"])

        if action == "uninstall":
            if revert:
                actions.extend(["install"])
            else:
                actions.extend(["uninstall"])

        return actions

    def implement_env_cfgs(self, action):
        logger.info("Implementing environments configuration")
        env_stats = {}
        all_env_acks = {}

        actions = self.augment_action(action)
        logger.info(f"Implementing environments actions {actions}")

        for envid, env_cfg in self.env_cfgs.items():
            self._proxy.load(env_cfg)
            env_acks, env_stat = self._proxy.implement(actions)

            env_stats[envid] = env_stat
            all_env_acks[envid] = env_acks

        all_acks = all([ack for ack in all_env_acks.values()])
        self.env_stats = env_stats

        messages = [stat.get("msg") for stat in env_stats.values()]
        logger.info("Replying messages")
        logger.info(f"{messages}")

        if all_acks:
            return True, messages
        else:
            return False, messages

    def stats_env_cfgs(self):
        return self.env_stats
