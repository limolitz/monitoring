#!/usr/bin/env python3
import subprocess
import datetime
import json
import configparser
import sys

def getFilesystemInfo(filesystem):
	proc = subprocess.Popen("df {} | grep {}".format(filesystem,filesystem), stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
	output, errors = proc.communicate()
	if len(errors) > 0:
		print("An error occured: {}".format(errors.decode("utf-8")),file=sys.stderr)
	parsedOutput = list(filter(None, output.decode("utf-8").split(" ")))
	used = int(parsedOutput[2])
	available = int(parsedOutput[3])
	print("Filesystem {} has {} used and {} available of {}.".format(filesystem,used,available,used+available))
	info = {
		"filesystem": filesystem,
		"used": used,
		"available": available,
		"total": used+available
	}
	return info

config = configparser.ConfigParser()
config.read('config.ini')
watchedFilesystemsPlain = config.get("disks", "watchedFilesystems")
watchedFilesystems = watchedFilesystemsPlain.split(',')
print("Watched filesystems: {}".format(watchedFilesystems))

spaceInfo = {}
for watchedFilesystem in watchedFilesystems:
	spaceInfo[watchedFilesystem] = getFilesystemInfo(watchedFilesystem)

mqttObject = {
	"topic": "diskspace",
	"measurements": spaceInfo
}

json = json.dumps(mqttObject)
print("Writing JSON: {}".format(json))
sender = subprocess.Popen([config.get("Paths", "mqttPath")], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
output, errors = sender.communicate(json.encode("utf-8"))
print(output,errors)