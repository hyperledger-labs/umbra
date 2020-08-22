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

        result_flag = True
        if self._connect():
            try:

                self.scp = SCPClient(self._client.get_transport())

                self.scp.put(
                    local_filepath, recursive=True, remote_path=remote_filepath
                )

                self._client.close()

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
                    "Command Done: %s, pid=%s, result: %s"
                    % (cmd, proc.pid, stdout.decode().strip())
                )
            else:
                ack = False
                msg = stderr.decode("utf-8")
                logger.debug(
                    "Command Failed: %s, pid=%s, result: %s"
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
        task = asyncio.create_task(self.process_call(command))
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(task)
        ack = results.get("ack", False)
        msg = results.get("msg", None)
        return ack, msg

    def copy_files(self, source, destination):
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

    def _workflow_start(self, name, info):
        cmd = "sudo umbra-{name} --uuid {uuid} --address {address} --debug &".format(
            name=name, uuid=info.get("uuid"), address=info.get("address")
        )
        ack, msg = self._plugin.execute_command(cmd)

        output = {
            "ack": ack,
            "msg": msg,
        }
        return output

    def _workflow_stop(self, name, info):
        cmd = "sudo pkill -9 umbra-{name}".format(name=name)
        ack, msg = self._plugin.execute_command(cmd)

        output = {
            "ack": ack,
            "msg": msg,
        }
        return output

    def _workflow_install_model(self):
        install_cmd = f"cd /tmp/umbra/source && sudo make install-{self.model}"
        ack_install, msg_install = self._plugin.execute_command(install_cmd)
        return ack_install, msg_install

    def _workflow_install(self, name, info):
        source = self.settings.get("source")
        destination = self.settings.get("destination")

        ack = self._plugin.copy_files(source, destination)

        if ack:
            clone_cmd = (
                "git clone https://github.com/raphaelvrosa/umbra /tmp/umbra/source"
            )
            ack_clone, msg_clone = self._plugin.execute_command(clone_cmd)

            install_cmd = "cd /tmp/umbra/source && sudo apt install -y make && sudo make requirements install-deps install"
            ack_install, msg_install = self._plugin.execute_command(install_cmd)

            ack_install_model, msg_install_model = self._workflow_install_model()

            ack = ack_clone and ack_install and ack_install_model
            msg = {**msg_clone, **msg_install, **msg_install_model}
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
        uninstall_cmd = "cd /tmp/umbra/source && sudo pip uninstall -y umbra"
        ack_uninstall, msg_uninstall = self._plugin.execute_command(uninstall_cmd)

        rm_cmd = "sudo rm -R /tmp/umbra/source"
        ack_rm, msg_rm = self._plugin.execute_command(rm_cmd)

        ack = ack_rm and ack_uninstall
        msg = {**msg_rm, **msg_uninstall}
        output = {
            "ack": ack,
            "msg": msg,
        }
        return output

    async def implement(self, actions):
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
        env_stats = {}
        all_env_acks = {}

        actions = self.augment_action(action)

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
