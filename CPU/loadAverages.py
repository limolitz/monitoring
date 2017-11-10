#!/usr/bin/env python3
import subprocess
import datetime
import json

# read new data
loadAverages = subprocess.Popen('/home/florin/bin/QuantifiedSelf/CPU/loadAverages.sh', stdout=subprocess.PIPE).stdout.read()
averages = []
print("Date: {}".format(datetime.datetime.utcnow()))
averages.append(datetime.datetime.utcnow().strftime("%s"))
for avg in str(loadAverages).rstrip().split(", "):
	averages.append(avg)
#print(averages)

# load old data
with open("/home/florin/bin/QuantifiedSelf/CPU/cpu.data") as f:
	content = f.readlines()

data = []
for item in content:
	items = item.rstrip().split("\t")
	#print(items)
	data.append(items)

data.append(averages)

# discard old data
data = data[-60:]

# append new data
content.append(averages)

#print(content)
with open("/home/florin/bin/QuantifiedSelf/CPU/cpu.data", "w") as myfile:
	for avg in data:
		myfile.write(avg[0]+"	"+avg[1]+"	"+avg[2]+"	"+avg[3]+"\n")

# write object for MQTT sending
mqttObject = {
	"topic": "cpu",
	"measurements": {
		"avg1": avg[1],
		"avg5": avg[2],
		"avg15": avg[3]
	}
}

json = json.dumps(mqttObject)
print("Writing JSON: {}".format(json))
sender = subprocess.Popen(["/home/florin/bin/mqttsend/mqttsend.sh"], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
sender.stdin.write(json)