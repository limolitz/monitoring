#!/usr/bin/env python3
import urllib.request
import re
import os
from dateutil.relativedelta import relativedelta
import pickle
import datetime
import time
import subprocess
import psutil

def findCaller():
	me = psutil.Process()
	parent = psutil.Process(me.ppid())
	return parent.cmdline()

def getIfManualCall():
	callerCmd = findCaller()
	if callerCmd[0] == "-zsh":
		return True
	return False

def debugPrint(output):
	if getIfManualCall():
		print(output)

def unimportantDevice(deviceName):
	unimportantDevices = ['Moto E', 'Tablet']
	if deviceName in unimportantDevices:
		debugPrint("Ignoring device {}".format(deviceName))
		return True
	return False

def readableNameOf(deviceName,quiet=False):
	readableNames = {'android-e53fd3d31e2': 'z1compact', 'Hanna': 'Hanna Laptop', 'android-45393a33648': 'Moto E', 'frost': 'frost', 'moneypenny': 'moneypenny', 'android-bc7e8ff9af1': 'Tablet', 'android-627a3a6eef0': 'Fairphone', 'android-4abaca69697': 'Z5 Compact'}
	if deviceName in readableNames:
		return readableNames[deviceName]
	else:
		if not(quiet):
			print("	No readable name of {} known.".format(deviceName))
		return deviceName

def readableNameMac(device,quiet=False):
	mac = device['mac']
	readableNames = {'84:8E:DF:54:40:13': 'z1compact', '00:71:CC:41:0B:D1': 'Hanna Laptop', 'F8:CF:C5:4F:FA:DA': 'Moto E', 'B8:27:EB:4A:D9:5E': 'frost', 'E8:2A:EA:27:48:C7': 'moneypenny', 'BC:6E:64:3D:4C:BA': 'Tablet', '6C:AD:F8:44:09:B3': 'Fairphone', '58:48:22:7E:3B:1B': 'Z5 Compact', 'C4:B3:01:D5:CD:F7': 'LS Retail Macbook', 'F0:79:60:B4:CE:BD': 'Matthias iPhone', '0C:3E:9F:58:5E:DF': 'Ellis iPhone', '08:74:02:13:43:BF': 'Renatas iPhone', '50:1A:C5:F5:76:23': 'Mathias Surface', '00:0C:29:37:6F:34': 'LS Retail VM Ubuntu', '24:7F:3C:06:57:D9': 'Annejet Android', '74:DE:2B:9D:46:B0': 'Annejet Laptop', '5C:F7:C3:C0:31:64': 'Franzi Android'}
	if mac in readableNames:
		return readableNames[mac]
	else:
		if not(quiet):
			debugPrint("	No readable name of {} known. Use self-given name {}.".format(mac,device['name']))
		return device['name']

def formatTimedifference(timeDifference):
	seconds = timeDifference.total_seconds()
	minutes = int(seconds / 60)
	hours = 0
	days = 0
	if minutes >= 60:
		hours = int(minutes/60)
		minutes = minutes - hours*60
	else:
		return "{:02}min".format(minutes)
	if hours >= 24:
		days = int(hours/24)
		hours = hours - days*24
		return "{}d {:02d}:{:02d}h".format(days,hours,minutes)
	else:
		return "{:02d}:{:02d}h".format(hours,minutes)

def formatTime(time):
	# todo: simplify format when today, an hour ago etc
	now = datetime.datetime.utcnow()
	if time.year != now.year:
		return time.strftime("%Y-%m-%d %H:%M")
	if time.month != now.month:
		return time.strftime("%d.%m %H:%M")
	if time.day != now.day:
		return time.strftime("%d.%m %H:%M")
	return time.strftime("today, %H:%M")

def pingDevice(device):
	ip = getIpFromMac(device['mac'])
	return pingIp(device['ip'],device)

def pingIp(ip,device,tries=1):
	for i in range(0,tries):
		debugPrint("Ping {} ({}/{}), {}. try".format(readableNameMac(device),ip,device['mac'],i))
		result = os.system("ping -qc 1 {} >/dev/null".format(ip))
		if result == 0:
			if i != 0:
				print("{}. Ping to {} ({}) successfull.".format(i,readableNameMac(device['mac'],True),ip))
			return True
		#time.sleep(3)
	return False

def sshTestDevice(ip):
	return os.system("ssh '{}' true > /dev/null".format(ip)) == 0

def getMacFromArp(ip):
	line = subprocess.Popen("/usr/sbin/arp -a | grep '{}' | grep -oP '[a-f\:0-9]{{17}}'".format(ip), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True).stdout.read().split()
	if len(line) > 0:
		return line[0].decode("utf-8").upper()
	else:
		return False

def getIpFromMac(mac):
	#debugPrint("Searching for IP of MAC {}".format(mac))
	line = subprocess.Popen("/usr/sbin/arp -na | grep -i '{}' | awk '{{print $2}}' | cut -c 2- | rev | cut -c 2- | rev".format(mac),  stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True).stdout.read().split()
	if len(line) > 0:
		return line[0].decode("utf-8")
	else:
		return False

def loadDevicelist():
	if os.path.isfile('devicelist.p'):
		with open('devicelist.p', 'rb') as pickleInput:
			devicelist = pickle.load(pickleInput)
			return devicelist
	else:
		return {}

def storeDevicelist(devices):
	with open('devicelist.p', 'wb') as output:
		pickle.dump(devices, output)

def takeOverInfo(key, deviceInfo):
	if key in deviceInfo:
		return deviceInfo[key]
	else:
		return None

def cameOnlineCheck(device):
	if unimportantDevice(readableNameMac(device)):
		return
	if 'lastState' in device:
		if device['lastState'] != 'up':
			if device['lastSeen'] is not None:
				timeDifference = datetime.datetime.utcnow()-device['lastSeen']

				print("{} -> 🌕. Last seen {} ({} ago).".format(readableNameMac(device),formatTime(device['lastSeen']),formatTimedifference(timeDifference)))
			else:
				if not(unimportantDevice(readableNameMac(device))):
					print("{} -> 🌕.".format(readableNameMac(device)))
	else:
		print("New device {} came online.".format(readableNameMac(device)))

def wentOfflineCheck(device):
	if unimportantDevice(readableNameMac(device)):
		return
	if 'lastState' in device:
		if device['lastState'] != 'down':
			if device['lastOffline'] is not None:
				timeDifference = datetime.datetime.utcnow()-device['lastOffline']
				print("{} -> 🌑. Online since {} ({} ago).".format(readableNameMac(device),formatTime(device['lastOffline']),formatTimedifference(timeDifference)))
			else:
				print("{} -> 🌑.".format(readableNameMac(device)))
	else:
		print("New device {} seen, but is offline.".format(readableNameMac(device)))

#print("Caller: {}, manual call? {}".format(findCaller(),getIfManualCall()))

devicelist = 'http://192.168.1.1/dhcp_list.stm'
devices = loadDevicelist()

manager = urllib.request.HTTPPasswordMgrWithDefaultRealm()
manager.add_password(None, devicelist, '', 'admin')
authHandler = urllib.request.HTTPBasicAuthHandler(manager)

opener = urllib.request.build_opener(authHandler)

urllib.request.install_opener(opener)

response = urllib.request.urlopen(devicelist)
html = response.read().decode('utf8')

print(html)

exit()

clients = re.search(r"new dhcpclient.*\)\)", html).group(0)

# split along elements
clientsList = clients[:-1].split("new dhcpclient")[1:]

for client in clientsList:
	# divide infos

	# cut off comma
	if client[-2:] == ', ':
		client = client[:-2]

	# cut off parentheses
	client = client[1:-1]

	# split along array entries
	clientSplit = client.split(', ')

	# cut off "
	clientSplit = list(map(lambda x: x[1:-1], clientSplit))

	#print(clientSplit)
	# name elements
	name = clientSplit[0]
	network = clientSplit[1]
	ip = clientSplit[2]
	mac = clientSplit[3]
	expireTime = int(clientSplit[4])
	lastConnect = relativedelta(seconds=86400-expireTime)
	debugPrint("- {} is on {} with the ip {} and the MAC {}, expire time: {}, last connect {}.".format(name,network,ip,mac,expireTime,lastConnect))

	# ping ip once to fill arp cache
	#pingIp(ip,1)

	# build entry
	deviceInfo = {'name': name, 'network': network, 'mac': mac, 'ip': ip, 'expireTime': expireTime, 'lastConnect': lastConnect}

	# check if there is already info to take over
	if mac in devices:
		deviceInfo['lastSeen'] = takeOverInfo('lastSeen', devices[mac])
		deviceInfo['lastOffline'] = takeOverInfo('lastOffline', devices[mac])
		deviceInfo['lastState'] = takeOverInfo('lastState', devices[mac])
		# a devices name changed
		if name != devices[mac]['name']:
			print("MAC {}/Name {} is also known as {}.".format(mac,devices[mac]['name'],name))
	else:
		print("New device {} with MAC {}. Pinging it to fill ARP cache.".format(name,mac))
		pingDevice(deviceInfo)
		deviceInfo['lastSeen'] = None
		deviceInfo['lastOffline'] = None
		deviceInfo['lastState'] = None
	devices[mac] = deviceInfo

# ping the devices
for deviceMac in devices:
	if deviceMac == "":
		continue
	device = devices[deviceMac]
	# TODO: check if IP and MAC match
	# first get IP from MAC
	macIp = getIpFromMac(device['mac'])
	if macIp == False:
		# look if IP is assigned to someone else
		debugPrint("X Device {} with MAC {} has no IP in ARP cache.".format(readableNameMac(device),device['mac']))
		# if we know an IP of the device
		# TODO? get IP from table info
		if 'ip' in device.keys():
			currentOwner = getMacFromArp(device['ip'])
			if currentOwner != False:
				debugPrint("X! Its IP {} is currenly owned by {}. Ignoring.".format(device['ip'],readableNameMac({'mac': currentOwner, 'name': currentOwner})))
				continue
			else:
				#print("XX The IP {} of {} is currenly not owned by anyone. Pinging.".format(device['ip'],readableNameMac(device)))
				pingIp(device['ip'],device)
	elif macIp != device['ip']:
		# mismatch between table IP and the one from the ARP cache. Should not happen
		print("! Ignoring device {} because its IP {} is not {} which is assigned to its MAC {}.".format(readableNameMac(device),device['ip'],macIp,device['mac']))
		continue
	if not 'ip' in device.keys():
		#print("! Device {} has no known IP. Ignoring.".format(readableNameMac(device)))
		continue
	# ping device
	if pingDevice(device):
		debugPrint("+ Host {} appears to be up.".format(readableNameMac(device)))
		cameOnlineCheck(device)
		devices[deviceMac]['lastSeen'] = datetime.datetime.now()
		devices[deviceMac]['lastState'] = 'up'
	else:
		debugPrint("+ Host {} appears to be down. Last connect ~{:02d}:{:02d}h ago. Last seen {}.".format(readableNameMac(device),device['lastConnect'].hours,device['lastConnect'].minutes,device['lastSeen']))
		wentOfflineCheck(device)
		devices[deviceMac]['lastState'] = 'down'
		devices[deviceMac]['lastOffline'] = datetime.datetime.now()


storeDevicelist(devices)
