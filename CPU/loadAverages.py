#!/usr/bin/env python3
import subprocess
import datetime
import json

# read new data
loadAverages = subprocess.Popen('/home/florin/bin/QuantifiedSelf/CPU/loadAverages.sh', stdout=subprocess.PIPE).stdout.read()
averages = []
for avg in str(loadAverages).rstrip().split(", "):
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
sender = subprocess.Popen(["/home/florin/bin/mqttsend/mqttsend.sh"], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
sender.stdin.write(json)