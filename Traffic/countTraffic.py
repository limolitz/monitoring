#!/usr/bin/env python3
# log traffic on unix
import subprocess
import sqlite3 as sql
import sys
sys.path.insert(0,'..')
import configparser
import json
import platform
from pathlib import Path

def getAllInterfaces():
	ip = subprocess.Popen(["ip", "-json", "link", "show"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	output, errors = ip.communicate()
	# no errors
	if len(errors) == 0:
		data = json.loads(output.decode("utf-8"))
		names = [entry["ifname"] for entry in data]
		return names
	else:
		# check if ip just doesn't support -json yet
		if "Option \"-json\" is unknown" in errors.decode("utf-8"):
			# fallback to plain output parsing
			# piping to grep
			# https://stackoverflow.com/questions/13332268/how-to-use-subprocess-command-with-pipes
			# grep output groups
			# https://unix.stackexchange.com/questions/13466/can-grep-output-only-specified-groupings-that-match
			ip = subprocess.Popen(["ip", "link" ,"show"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			grep = subprocess.Popen(["grep", "-oP", "^[0-9]*: (\\K[a-z0-9]*)"], stdin=ip.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			ip.stdout.close()
			output, errors = grep.communicate()
			if errors:
				print(errors, file=sys.stderr)
			return output.decode("utf-8").splitlines()
		else:
			print("Error on ip call: {}".format(errors.decode("utf-8")), file=sys.stderr)

def trafficInBytes(interface):
	if platform.system() == "Darwin":
		return trafficInBytesMac(interface)
	else:
		return trafficInBytesLinux(interface)

def trafficInBytesLinux(interface):
	bytes = []
	rx_bytes = Path("/sys/class/net/{}/statistics/rx_bytes".format(interface))
	tx_bytes = Path("/sys/class/net/{}/statistics/tx_bytes".format(interface))
	if rx_bytes.is_file() and tx_bytes.is_file():
		with rx_bytes.open("rb") as f:
			content = f.read()
			bytes.append(int(content))
		with tx_bytes.open("rb") as f:
			content = f.read()
			bytes.append(int(content))
		return bytes
	return None

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
	if interfaces is None:
		print("Error on getAllInterfaces.", file=sys.stderr)
		exit(1)
	for interface in interfaces:

		uptime = uptimeInSeconds(selfPath)
		traffic = trafficInBytes(interface)
		if traffic is None:
			print("Error on reading data for interface {}.".format(interface))
			continue

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
		print(output.decode("utf-8"))
		if errors:
			print(errors.decode("utf-8"), file=sys.stderr)
