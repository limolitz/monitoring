#!/usr/bin/env python3
# log traffic on unix
import subprocess
import sqlite3 as sql
import sys
sys.path.insert(0,'..')
import configparser
import json
import platform

def getAllInterfaces():
	ip = subprocess.Popen(["ip", "-json", "link", "show"],stdout=subprocess.PIPE)
	output, errors = ip.communicate()
	data = json.loads(output.decode("utf-8"))
	names = [entry["ifname"] for entry in data]
	return names

def trafficInBytes(interface):
	if platform.system() == "Darwin":
		return trafficInBytesMac(interface)
	else:
		return trafficInBytesLinux(interface)

def trafficInBytesLinux(interface):
	bytes = []
	with open("/sys/class/net/{}/statistics/rx_bytes".format(interface), "rb") as f:
		content = f.read()
		bytes.append(int(content))
	with open("/sys/class/net/{}/statistics/tx_bytes".format(interface), "rb") as f:
		content = f.read()
		bytes.append(int(content))
	return bytes

def trafficInBytesMac(interface):
	netstat = subprocess.Popen(["netstat","-b","-n","-I",interface],stdout=subprocess.PIPE)
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

	interfaces = getAllInterfaces()
	for interface in interfaces:

		uptime = uptimeInSeconds(selfPath)
		traffic = trafficInBytes(interface)
		mqttObject = {
			"topic": "traffic",
			"name": interface,
			"measurements": {
				"uptime": uptime,
				"{}_rx_bytes".format(interface): int(traffic[0]),
				"{}_tx_bytes".format(interface): int(traffic[1])
			}
		}
		jsonObject = json.dumps(mqttObject)
		print("Writing JSON: {}".format(jsonObject))
		sender = subprocess.Popen([config.get("Paths", "mqttPath")], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
		output, errors = sender.communicate(jsonObject.encode("utf-8"))
		print(output.decode("utf-8"),errors.decode("utf-8"))
