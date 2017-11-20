#!/usr/bin/env python3
# log traffic on unix
import subprocess
import sqlite3 as sql
import datetime
import sys
sys.path.insert(0,'..')
import configparser
import json
import platform

def trafficInBytes(selfPath,config):
	if platform.system() == "Darwin":
		return trafficInBytesMac(selfPath,config)
	else:
		return trafficInBytesLinux(selfPath,config)

def trafficInBytesLinux(selfPath,config):
	bytes = []
	interface = format(config.get("Paths", "interface"))
	with open("/sys/class/net/{}/statistics/rx_bytes".format(interface), "rb") as f:
		content = f.read()
		bytes.append(int(content))
	with open("/sys/class/net/{}/statistics/tx_bytes".format(interface), "rb") as f:
		content = f.read()
		bytes.append(int(content))
	return bytes

def trafficInBytesMac(selfPath,config):
	netstat = subprocess.Popen(["netstat","-b","-n","-I",config.get("Paths", "interface")],stdout=subprocess.PIPE)
	output, errors = netstat.communicate()
	# split by newlines
	lines = output.decode("utf-8").split('\n')
	# remove empty entries
	parts = list(filter(None, lines[1].split(" ")))
	ibytes = parts[6]
	obytes = parts[9]
	bytes = [ibytes,obytes]
	return bytes

def uptimeInSeconds(selfPath):
	# get uptime in seconds
	uptime = int(subprocess.Popen("{}/getUptimeSeconds.sh".format(selfPath), stdout=subprocess.PIPE).stdout.read())
	print('Uptime: {}s'.format(uptime))
	return uptime

if __name__ == '__main__':
	config = configparser.ConfigParser()
	config.read('config.ini')
	selfPath = config.get("Paths", "selfPath")

	uptime = uptimeInSeconds(selfPath)
	traffic = trafficInBytes(selfPath,config)
	mqttObject = {
		"topic": "traffic",
		"measurements": {
			"uptime": uptime,
			"trafficReceived": int(traffic[0]),
			"trafficTransmitted": int(traffic[1])
		}
	}
	json = json.dumps(mqttObject)
	print("Writing JSON: {}".format(json))
	sender = subprocess.Popen([config.get("Paths", "mqttPath")], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
	output, errors = sender.communicate(json.encode("utf-8"))
	print(output.decode("utf-8"),errors.decode("utf-8"))
