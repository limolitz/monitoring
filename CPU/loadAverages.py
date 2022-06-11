#!/usr/bin/env python3

import subprocess
import json
import configparser
import logging
import logging.config


config = configparser.ConfigParser()
config.read('config.ini')

logging.config.fileConfig(config)

_logger = logging.getLogger(__name__)

# read new data
with open('/proc/loadavg') as file:
    data = file.read()

averages = data.split(" ")[:3]

# write object for MQTT sending
mqttObject = {
    "topic": "cpu",
    "measurements": {
        "avg1": averages[0],
        "avg5": averages[1],
        "avg15": averages[2]
    }
}

json = json.dumps(mqttObject)
_logger.debug("Writing JSON: {}".format(json))
sender = subprocess.Popen(
    [config.get("Paths", "mqttPath")],
    stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE
)
output, errors = sender.communicate(json.encode("utf-8"))
_logger.debug(output.decode("utf-8"))
if errors:
    _logger.error(errors.decode("utf-8"))
    exit(1)
