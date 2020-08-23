import os
import json
import logging
import paramiko
import traceback
import asyncio
from scp import SCPClient, SCPException


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
            self._client.set_missing_host_key_policy(paramiko.WarningPolicy())

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

    def execute_command(self, command):
        """Execute a command on the remote host."""

        self.ssh_output = None
        result_flag = True
        result = ""

        try:
            if self._connect():
                logger.info("Executing command --> {}".format(command))
                _, stdout, stderr = self._client.exec_command(command, timeout=60)
                self.ssh_output = stdout.read()
                self.ssh_error = stderr.read()

                if self.ssh_error:
                    logger.info(
                        f"Problem occurred while running command: error {self.ssh_error}"
                    )
                    # result_flag = False
                    result = self.ssh_error

                if self.ssh_output:
                    logger.info(
                        f"Command execution completed successfully: output {self.ssh_output}"
                    )
                    result = self.ssh_output

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
    def __init__(self):
        pass

    async def process_call(self, cmd):
        """Performs the async execution of cmd in a subprocess
        
        Arguments:
            cmd {string} -- The full command to be called in a subprocess shell
        
        Returns:
            dict -- The output of the cmd execution containing stdout and stderr fields
        """
        logger.debug(f"Calling subprocess command: {cmd}")
        out = {}
        try:
            proc = await asyncio.create_subprocess_shell(
                cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await proc.communicate()

            if proc.returncode == 0:
                ack = True
                msg = stdout.decode("utf-8")
                logger.debug(
                    "Command execution completed successfully: %s, pid=%s, output: %s"
                    % (cmd, proc.pid, stdout.decode().strip())
                )
            else:
                ack = False
                msg = stderr.decode("utf-8")
                logger.debug(
                    "Problem occurred while running command: %s, pid=%s, error: %s"
                    % (cmd, proc.pid, stderr.decode().strip())
                )

            out = {
                "ack": ack,
                "msg": msg,
            }

        except OSError as excpt:
            logger.debug(f"Could not call cmd {cmd} - exception {excpt}")

            out = {
                "ack": False,
                "msg": proc.exception(),
            }
        except asyncio.CancelledError:
            logger.debug("cancel_me(): call task cancelled")
            raise

        finally:
            return out

    def execute_command(self, command):
        # task = asyncio.create_task(self.process_call(command))
        # loop = asyncio.get_event_loop()
        # results = loop.run_until_complete(task)
        results = asyncio.run(self.process_call(command))
        ack = results.get("ack", False)
        msg = results.get("msg", None)
        return ack, msg

    def copy_files(self, source, destination):
        logger.info(f"Local-Copying files from {source} to {destination}")
        return True


class Proxy:
    def __init__(self):
        self._remote_plugin = RemotePlugin()
        self._local_plugin = LocalPlugin()
        self._plugin = None
        self.model = ""
        self.host_cfg = {}
        self.components = {}
        self.settings = {}

    def load(self, env_cfg):
        logger.info(f"Loading environment config")
        self.remote = env_cfg.get("remote", False)

        if self.remote:
            self.host_cfg = env_cfg.get("host")
            self._remote_plugin.cfg(self.host_cfg)
            self._plugin = self._remote_plugin
        else:
            self._plugin = self._local_plugin

        self.components = env_cfg.get("components")
        self.settings = env_cfg.get("settings")
        self.model = env_cfg.get("model")

        logger.info(
            f"Environment: id {env_cfg.get('id')}, model {env_cfg.get('model')}, remote {env_cfg.get('remote')}"
        )
        logger.info(f"Components: {env_cfg.get('components')}")

    def _workflow_start(self, name, info):
        logger.info(f"Workflow start: component {name}")

        cmd = "sudo umbra-{name} --uuid {uuid} --address {address} --debug &".format(
            name=name, uuid=info.get("uuid"), address=info.get("address")
        )
        ack, msg = self._plugin.execute_command(cmd)

        output = {
            "ack": ack,
            "msg": msg,
        }
        logger.info(f"Stats: {ack} - msg: {msg}")
        return output

    def _workflow_stop(self, name, info):
        logger.info(f"Workflow stop: component {name}")

        cmd = "sudo pkill -9 umbra-{name}".format(name=name)
        ack, msg = self._plugin.execute_command(cmd)

        output = {
            "ack": ack,
            "msg": msg,
        }
        logger.info(f"Stats: {ack} - msg: {msg}")
        return output

    def _workflow_model(self, action):
        logger.info(f"Workflow model {self.model} - action {action}")
        action_cmd = f"cd /tmp/umbra/source && sudo make {action}-{self.model}"
        ack_action, msg_action = self._plugin.execute_command(action_cmd)
        logger.info(f"Stats: {ack_action} - msg: {msg_action}")
        return ack_action, msg_action

    def _workflow_source_files(self, action):
        logger.info(f"Workflow source files - action {action}")

        if action == "install":
            clone_cmd = (
                "git clone https://github.com/raphaelvrosa/umbra /tmp/umbra/source"
            )
            ack_source_files, msg_source_files = self._plugin.execute_command(clone_cmd)

        if action == "uninstall":
            rm_cmd = "sudo rm -R /tmp/umbra/source"
            ack_source_files, msg_source_files = self._plugin.execute_command(rm_cmd)

        return ack_source_files, msg_source_files

    def _workflow_install(self, name, info):
        logger.info(f"Workflow install")

        source = self.settings.get("source")
        destination = self.settings.get("destination")
        ack = self._plugin.copy_files(source, destination)

        if ack:
            ack_clone, msg_clone = self._workflow_source_files("install")
            logger.info("Executing command - install requirements, deps, umbra install")
            install_cmd = "cd /tmp/umbra/source && sudo apt install -y make && sudo make requirements install-deps install"
            ack_install, msg_install = self._plugin.execute_command(install_cmd)

            ack_install_model, msg_install_model = self._workflow_model("install")

            ack = ack_clone and ack_install and ack_install_model
            msg = {
                "clone": msg_clone,
                "install": msg_install,
                "install-model": msg_install_model,
            }
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

    def _workflow_uninstall(self, name, info):
        logger.info(f"Workflow uninstall")

        ack_uninstall_model, msg_uninstall_model = self._workflow_model("uninstall")

        logger.info(f"Executing command - uninstall umbra")
        uninstall_cmd = "cd /tmp/umbra/source  && sudo make uninstall uninstall-deps"
        ack_uninstall, msg_uninstall = self._plugin.execute_command(uninstall_cmd)

        ack_rm, msg_rm = self._workflow_source_files("uninstall")

        ack = ack_rm and ack_uninstall and ack_uninstall_model
        msg = {
            "remove": msg_rm,
            "uninstall": msg_uninstall,
            "uninstall-model": msg_uninstall_model,
        }
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
        logger.info(f"Implementing actions")

        action_outputs = {}

        for action in actions:
            for name, info in self.components.items():
                action_output = {}

                if action in ["start"]:
                    action_output = self._workflow_start(name, info)

                if action in ["stop"]:
                    action_output = self._workflow_stop(name, info)

                if action in ["install"]:
                    action_output = self._workflow_install(name, info)

                if action in ["uninstall"]:
                    action_output = self._workflow_uninstall(name, info)

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
        envs = topology.get_environments()
        setts = topology.get_settings()
        model = topology.get_model()

        env_cfgs = {}

        for envid, env in envs.items():

            env_cfg = {
                "id": envid,
                "model": model,
                "remote": env.get("remote", False),
                "settings": {"source": setts, "destination": setts,},
                "components": env.get("components"),
                "host": env.get("host", {}),
            }

            env_cfgs[envid] = env_cfg

        self.env_cfgs = env_cfgs

    def augment_action(self, action, revert=False):
        actions = []

        if action == "start":
            if revert:
                actions.extend(["stop", "uninstall"])
            else:
                actions.extend(["install", "start"])

        if action == "stop":
            if revert:
                actions.extend(["install", "start"])
            else:
                actions.extend(["stop", "uninstall"])

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

        if all_acks:
            return True
        else:
            return False

    def stats_env_cfgs(self):
        return self.env_stats
