import logging
import json
import argparse
import subprocess
import time
from datetime import datetime


logger = logging.getLogger(__name__)


def _parse(out, err):
    """Parses the process output

    Arguments:
        out {bytes} -- The stdout of the process
        err {bytes} -- The stderr of the process

    Returns:
        tuple -- (string, string) Both process out and err 
        in string format (utf-8)
    """
    output = out.decode("UTF-8")
    error = err.decode("UTF-8")
    return output, error


def start_process(args, shell=False):
    """Run a process using the provided args
    if stop is true it waits the timeout specified
    before stopping the process, otherwise waits till
    the process stops

    Arguments:
        args {list} -- A process command to be called

    Returns:
        process/None -- A process instance if executed correctly,
        or None otherwise
    """

    try:
        p = subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=shell,
        )
        process = p

    except OSError:
        process = None
    finally:

        return process


def stop_process(p):
    """Stops the running process

    Arguments:
        p {process} -- A process object

    Returns:
        bool -- If the process was stopped
        correctly or not
    """
    if p:
        pid = p.pid
        p.kill()
        out, err = p.communicate()
        code = p.returncode
        logger.debug(f"Process {pid} stopped - return code {code}")
        # logger.debug(f"Process {pid} stopped - out {out}, err {err}")
        return True
    return False

