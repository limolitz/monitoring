#!/usr/bin/env python3.6
import subprocess
import datetime
import configparser
import json
import platform

def getRAMofProcess(processName):
	proc = subprocess.Popen('ps -C '+processName+' -o rss=', stdout=subprocess.PIPE, shell=True)
	sums = 0
	for line in proc.stdout:
		sums += int(line.rstrip())
	return sums

def getRAMofProcessMac(programName,output):
	#print(output,programName)
	sums = 0
	for line in output:
		decodedLine = line.decode('utf-8')
		if programName in decodedLine:
			#print(decodedLine)
			pid = list(filter(None, decodedLine.split(' ')))[0]
			print("{} Parent PID: {}".format(programName,pid))
			ps = subprocess.Popen('ps -o rss=,pid= -g {}'.format(pid), stdout=subprocess.PIPE, shell=True)
			output, errors = ps.communicate()
			for line in output.splitlines():
				parsedOutput = line.decode('utf-8')
				if parsedOutput != '':
					ps2Output = list(filter(None, parsedOutput.split(' ')))
					#print(ps2Output)
					rss = ps2Output[0]
					childPid = ps2Output[1]
					print(" - Child PID {} RSS: {}".format(childPid,rss))
					sums += int(rss)
				else:
					print("PID {} is empty.".format(pid))
	print("Total RSS of {}: {}".format(programName,sums))
	return sums

config = configparser.ConfigParser()
config.read('config.ini')
watchedProgramsPlain = config.get("Programs", "interesting")
watchedPrograms = watchedProgramsPlain.split(',')
#print("Watched programs: {}".format(watchedPrograms))

# read new data
print(platform.system())
if platform.system() == "Darwin":
	# Mac reports in bytes
	memTotal = int(subprocess.Popen('/usr/sbin/sysctl hw.memsize | /usr/local/bin/ggrep -o "[0-9]*"',stdout=subprocess.PIPE, shell=True).stdout.read())/1024
	print("Total: {}.".format(memTotal))
	# https://apple.stackexchange.com/a/94258
	memFree = int(subprocess.Popen("vm_stat | perl -ne '/page size of (\d+)/ and $size=$1; /Pages\s+([^:]+)[^\d]+(\d+)/ and printf(\"%-16s % 16d b\n\", \"$1:\", $2 * $size);\' | /usr/local/bin/ggrep 'free:' | /usr/local/bin/ggrep -o '[0-9]*'",stdout=subprocess.PIPE, shell=True).stdout.read())/1024
	print("Free: {}".format(memFree))
else:
	# Linux reports in kB
	memTotal = int(subprocess.Popen('cat /proc/meminfo | grep -o "MemTotal.*" | grep -o "[0-9]*"', stdout=subprocess.PIPE, shell=True).stdout.read())
	memFree = int(subprocess.Popen('cat /proc/meminfo | grep -o "MemFree.*" | grep -o "[0-9]*"', stdout=subprocess.PIPE, shell=True).stdout.read())

memUsed = memTotal - memFree


memoryInfo = {
	"total": memTotal,
	"free": memFree,
	"used": memUsed
}
if platform.system() == "Darwin":
	macInfo = subprocess.Popen(["/bin/ps","-o", "pid,command", "-x"], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
	output, errors = macInfo.communicate()
	#print(output)
	for programName in watchedPrograms:
		memoryInfo[programName] = getRAMofProcessMac(programName,output.splitlines())
else:
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
