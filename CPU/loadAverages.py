#!/usr/bin/env python3
import subprocess
import datetime

# read new data
loadAverages = subprocess.Popen('/home/florin/bin/QuantifiedSelf/CPU/loadAverages.sh', stdout=subprocess.PIPE).stdout.read()
averages = []
print(datetime.datetime.utcnow())
averages.append(datetime.datetime.utcnow().strftime("%s"))
for avg in str(loadAverages).rstrip().split(", "):
	avg = avg.replace(",", ".")
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
