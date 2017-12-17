#!/usr/bin/env python3.6
import subprocess
import datetime
import configparser
import json

def getRAMofProcess(processName):
	proc = subprocess.Popen('ps -C '+processName+' -o rss=', stdout=subprocess.PIPE, shell=True)
	sums = 0
	for line in proc.stdout:
		sums += int(line.rstrip())
	return sums

config = configparser.ConfigParser()
config.read('config.ini')
watchedProgramsPlain = config.get("Programs", "interesting")
watchedPrograms = watchedProgramsPlain.split(',')
#print("Watched programs: {}".format(watchedPrograms))

# read new data
memTotal = int(subprocess.Popen('cat /proc/meminfo | grep -o "MemTotal.*" | grep -o "[0-9]*"', stdout=subprocess.PIPE, shell=True).stdout.read())
memFree = int(subprocess.Popen('cat /proc/meminfo | grep -o "MemFree.*" | grep -o "[0-9]*"', stdout=subprocess.PIPE, shell=True).stdout.read())
memUsed = memTotal - memFree


memoryInfo = {
	"total": memTotal,
	"free": memFree,
	"used": memUsed
}
for programName in watchedPrograms:
	memoryInfo[programName] = getRAMofProcess(programName)


mqttObject = {
	"topic": "ram",
	"measurements": memoryInfo
}

json = json.dumps(mqttObject)
print("Writing JSON: {}".format(json))
sender = subprocess.Popen([config.get("Paths", "mqttPath")], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
output, errors = sender.communicate(json.encode("utf-8"))
print(output,errors)