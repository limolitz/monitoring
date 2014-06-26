#!/usr/bin/env python3
import subprocess
import datetime

def getRAMofProcess(processName):
	proc = subprocess.Popen('ps -C '+processName+' -o rss=', stdout=subprocess.PIPE, shell=True)
	print(memTotal)
	sums = 0
	for line in proc.stdout:
		#the real code does filtering here
		sums += int(line.rstrip())
	#print(sums)
	return sums
   

# read new data
memTotal = int(subprocess.Popen('cat /proc/meminfo | grep -o "MemTotal.*" | grep -o "[0-9]*"', stdout=subprocess.PIPE, shell=True).stdout.read())
memFree = int(subprocess.Popen('cat /proc/meminfo | grep -o "MemFree.*" | grep -o "[0-9]*"', stdout=subprocess.PIPE, shell=True).stdout.read())
memUsed = memTotal - memFree

# processes
firefox = getRAMofProcess('firefox')
chrome = getRAMofProcess('chrome')
print("Firefox: "+str(firefox))
print("Chrome: "+str(chrome))
print('Date: '+str(datetime.datetime.utcnow()))
memValues = []
memValues.append(datetime.datetime.utcnow().strftime("%s"))
memValues.append(memTotal)
memValues.append(memFree)
memValues.append(memUsed)
memValues.append(firefox)
memValues.append(chrome)
#print(memUsed)
print(memValues)

# load old data
with open("/home/florin/bin/QuantifiedSelf/RAM/ram.data") as f:
	content = f.readlines()

data = []
for item in content:
	items = item.rstrip().split("\t")
	#print(items)
	data.append(items)

data.append(memValues)

# discard old data
data = data[-60:]

# append new data
content.append(memValues)

#print(content)
with open("/home/florin/bin/QuantifiedSelf/RAM/ram.data", "w") as myfile:
	for value in data:
		myfile.write(str(value[0])+"	"+str(value[1])+"	"+str(value[2])+"	"+str(value[3])+"	"+str(value[4])+"	"+str(value[5])+"\n")
