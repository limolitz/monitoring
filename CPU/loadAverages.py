#!/usr/bin/env python3
import subprocess
import datetime
import json
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

# read new data
loadAveragesProcess = subprocess.Popen('./loadAverages.sh', stdout=subprocess.PIPE,stderr=subprocess.PIPE)
loadAverages, errors = loadAveragesProcess.communicate()
averages = []
for avg in loadAverages.decode("utf-8").rstrip().split(", "):
	averages.append(avg)

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
print("Writing JSON: {}".format(json))
sender = subprocess.Popen([config.get("Paths", "mqttPath")], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
output, errors = sender.communicate(json.encode("utf-8"))
print(output.decode("utf-8"),errors.decode("utf-8"))