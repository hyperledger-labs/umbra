#!/usr/bin/env python3.7

import os
import sys
import logging
import re
import subprocess
from shutil import which
from datetime import date

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

brokerlog_path = "logs/broker.log"
report_path = "logs/REPORT.log"

OUT = ""

OUT += "=============================================\n"
OUT += "===       Simulation Report Summary       ===\n"
OUT += "=============================================\n"
OUT += "\n\n"

def get_ts(line):
    # 2020-08-23 15:12:10,119 [INFO] umbra.broker.plugins.fabric
    # from log format above, timestamp field is at 2nd field
    out = " " + line.split(' ')[1]
    return out

def parse_dot(line):
    global OUT
    OUT += "\n\n\n"
    part = line.partition("DOT: ")

    res = ""
    if which("graph-easy"):
        proc = subprocess.run(["graph-easy"], stdout=subprocess.PIPE, input=part[2], encoding='ascii')
        res = proc.stdout
    else:
        res = "Install Perl script `sudo cpanm Graph::Easy` to parse Dot format"

    OUT += "Topology at" + get_ts(part[0]) + ":\n\n"
    OUT += res + "\n\n\n"

def parse_fabric_cfg(line):
    global OUT
    part = line.partition("FABRIC_CONFIG: ")
    OUT += part[2]

def parse_fabric_ev(line):
    global OUT
    ts = get_ts(line)
    part = line.partition("FABRIC_EV:")
    OUT += "Fabric_event response at" + ts + " " + part[2]

def parse_environment_ev(line):
    global OUT
    part = line.partition("START call_scenario:")
    ts = get_ts(line)
    OUT += "Executing environment_event at" + ts + " " + part[2]

with open(brokerlog_path, "r") as file:
    for line in file:
        if "FABRIC_CONFIG" in line:
            parse_fabric_cfg(line)

        if ": FABRIC_EV:" in line: # results from executing Fabric event
            parse_fabric_ev(line)

        if "START call_scenario:" in line:
            parse_environment_ev(line)

        if "Scheduling plugin fabric" in line:
            part = line.split(' ')
            OUT += f"Scheduling fabric event at: {part[1]}\n"

        if "Calling at" in line:
            part = line.partition("Calling at ")
            OUT += "   " + part[2]

        if "DOT" in line: # topology in DOT format
            parse_dot(line)

with open(report_path, 'w') as report_file:
    report_file.write(OUT)
