#!/usr/bin/env python3.7
#-*- coding: UTF-8 -*-

import urllib.request
import urllib.parse
import re
import os
import pickle
import datetime
import time
import subprocess
import psutil
from bs4 import BeautifulSoup
import configparser
import json
import copy
import http.client, http.cookiejar
import asyncio

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
		print('D: {}'.format(output))

def unimportantDevice(deviceName):
	unimportantDevices = ['Florin Moto E', 'Tablet']
	if deviceName in unimportantDevices:
		debugPrint("Ignoring unimportant device {}".format(deviceName))
		return True
	return False

def readableNameOf(device,quiet=False):
	name = readableNameMac(device['mac'])
	if name != False:
		return name
	else:
		if not(quiet):
			debugPrint("	No readable name of {} known. Use self-given name {}.".format(device['mac'],device['name']))
		return device['name']

def readableNameMac(mac):
	config = configparser.ConfigParser(delimiters='=')
	config.read('config.ini')
	if not isinstance(mac, str):
		return False
	try:
		readableName = config.get("Devices", mac)
		return readableName
	except configparser.NoOptionError as e:
		return False


def formatTimedifference(timeDifference):
	if isinstance(timeDifference,datetime.timedelta):
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
	else:
		debugPrint("Unknown object class {}: {}".format(type(timeDifference),timeDifference))
		return "NULL"

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

async def pingDeviceAsync(device):
	ip = getIpFromMac(device['mac'])
	return (device,await pingIpAsync(device['ip'],device))

async def pingIpAsync(ip,device,tries=1):
	for i in range(0,tries):
		debugPrint("Ping {} ({}/{}), {}. try of {}".format(readableNameOf(device),ip,device['mac'],i,tries))
		# -q: quiet
		# -c 1: one try
		# -W 3: timeout 3 secs
		result = os.system("ping -qc 1 -W 3 {} >/dev/null".format(ip))
		if result == 0:
			if i != 0:
				print("{}. Ping to {} ({}) successfull.".format(i,readableNameOf(device['mac'],True),ip))
			return True
		#time.sleep(3)
	return False

def pingDevice(device):
	ip = getIpFromMac(device['mac'])
	return pingIp(device['ip'],device)

def pingIp(ip,device,tries=1):
	for i in range(0,tries):
		debugPrint("Ping {} ({}/{}), {}. try of {}".format(readableNameOf(device),ip,device['mac'],i,tries))
		# -q: quiet
		# -c 1: one try
		# -W 3: timeout 3 secs
		result = os.system("ping -qc 1 -W 3 {} >/dev/null".format(ip))
		if result == 0:
			if i != 0:
				print("{}. Ping to {} ({}) successfull.".format(i,readableNameOf(device['mac'],True),ip))
			return True
		#time.sleep(3)
	return False

def sshTestDevice(ip):
	return os.system("ssh '{}' true > /dev/null".format(ip)) == 0

def getMacFromArp(ip):
	line = subprocess.Popen("/usr/sbin/arp -an | grep '{}' | grep -oP '[a-f\:0-9]{{17}}'".format(ip), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True).stdout.read().split()
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

def jsonifyDates(device,keys):
	for key in keys:
		if key in device:
			dateToFormat = device[key]
			if dateToFormat is not None:
				if isinstance(dateToFormat, datetime.datetime):
					device[key] = dateToFormat.strftime("%s")
				else:
					print("Unknown instance of {} on key {}. Setting to none.".format(type(dateToFormat),key))
					device[key] = None
	return device

def sanitizeDevice(device,deviceMac):
	device['mac'] = deviceMac
	device['readableName'] = readableNameMac(deviceMac)
	device = jsonifyDates(device,['lastOffline', 'lastSeen'])
	return device

def mqttSendAllDevices(devices):
	devicesInfo = {}
	for deviceMac in devices.keys():
		# make deepcoyp so we don't change anything in the existing objects
		devicesInfo[deviceMac] = sanitizeDevice(copy.deepcopy(devices[deviceMac]),deviceMac)

	mqttDict = {
		"topic": "devicesInNetwork",
		"measurements": devicesInfo
	}
	#print(mqttDict)
	mqttSend(mqttDict)

def mqttSendStatusChange(deviceInfo):
	return
	print(deviceInfo)
	message = deviceInfo['message']
	device = deviceInfo['device']

	mqttDict = {
		"topic": "devicesInNetworkStatusChange",
		"measurements": {
			"message": message,
			"device": sanitizeDevice(copy.deepcopy(device))
		}
	}

	#mqttSend(mqttDict)

def mqttSend(jsonDict):
	config = configparser.ConfigParser(delimiters='=')
	config.read('config.ini')
	jsonData = json.dumps(jsonDict)
	#debugPrint("Writing JSON: {}".format(jsonData))
	sender = subprocess.Popen([config.get("Paths", "mqttPath")], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
	output, errors = sender.communicate(jsonData.encode("utf-8"))
	#debugPrint("Output: {}, errors: {}".format(output,errors))

def checkIfMacInDeviceList(devices,mac):
	for device in devices:
		if mac == device['mac']:
			return True
	return False

def takeOverInfo(key, deviceInfo):
	if key in deviceInfo:
		return deviceInfo[key]
	else:
		return None

def cameOnlineCheck(device):
	message = None
	if unimportantDevice(readableNameOf(device)):
		return
	if 'lastState' in device:
		if device['lastState'] != 'up':
			if device['lastSeen'] is not None:
				timeDifference = datetime.datetime.utcnow()-device['lastSeen']
				message = "{} ⇑. Last seen {} ({} ago).".format(readableNameOf(device),formatTime(device['lastSeen']),formatTimedifference(timeDifference))

			else:
				if not(unimportantDevice(readableNameOf(device))):
					message = "{} ⇑.".format(readableNameOf(device))
	else:
		message = "New device {} came online.".format(readableNameOf(device))
	if message is not None:
		deviceInfo = {
			'device': device,
			'message': message
		}
		mqttSendStatusChange(deviceInfo)

def wentOfflineCheck(device):
	message = None
	if unimportantDevice(readableNameOf(device)):
		return
	if 'lastState' in device:
		if device['lastState'] != 'down':
			if device['lastOffline'] is not None and isinstance(device['lastOffline'],datetime.datetime):
				timeDifference = datetime.datetime.utcnow()-device['lastOffline']
				message ="{} ⇓. Online since {} ({} ago).".format(readableNameOf(device),formatTime(device['lastOffline']),formatTimedifference(timeDifference))
			else:
				message = "{} ⇓.".format(readableNameOf(device))
	else:
		message = "New device {} seen, but is offline.".format(readableNameOf(device))
	if message is not None:
		deviceInfo = {
			'device': device,
			'message': message
		}
		mqttSendStatusChange(deviceInfo)

def loadDevicesFromNmap():
	clients = []
	line = subprocess.Popen("/usr/bin/nmap -sn 192.168.1.* -oX -", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True).stdout.read()
	#print(line)
	soup = BeautifulSoup(line, 'lxml-xml')
	for host in soup.find_all('host'):
		ip = host.find('address')['addr']
		if host.find('hostname') is not None:
			hostname = host.find('hostname')['name']
		else:
			print("Hostname is none for {}.".format(ip))
		mac = getMacFromArp(ip)
		if mac == False:
			if hostname == "frost.lan":
				mac = 'B8:27:EB:4A:D9:5E'
			else:
				print("Mac is none for {}.".format(hostname))
		if readableNameMac(mac) != False:
			hostname = readableNameMac(mac)
		#print("{} with IP {} and MAC {}".format(hostname,ip,mac))
		clients.append({'name': hostname, 'mac': mac, 'ip': ip})

	return clients

async def main():
	devices = loadDevicelist()
	clientsList = loadDevicesFromNmap()

	for client in clientsList:
		# divide infos
		# name elements
		name = client['name']
		ip = client['ip']
		mac = client['mac']
		debugPrint("- {} ({}) with the ip {} and the MAC {}".format(readableNameMac(mac),name,ip,mac))

		# build entry
		deviceInfo = {'name': name, 'mac': mac, 'ip': ip}

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

	# build the futures to ping the devices
	futures = []
	for deviceMac in devices:
		if deviceMac == "":
			continue
		device = devices[deviceMac]
		if 'lastConnectDiff' in device.keys():
			del(device['lastConnectDiff'])
		if 'lastConnect' in device.keys():
			del(device['lastConnect'])
		debugPrint('Checking if we can ignore the device {} ({}):'.format(readableNameMac(device['mac']),device['name']))
		if not(checkIfMacInDeviceList(clientsList,deviceMac)) and device['lastState'] != 'up':
			debugPrint('	This device is currently not known to the router and its last known state was {}.'.format(device['lastState']))
			if device['lastSeen'] is None:
				debugPrint('	Device has no last seen info. Ignoring.')
				continue

			lastSeenDiff = datetime.datetime.now() - device['lastSeen']
			# check devices seen in the last week
			checkPeriod = datetime.timedelta(seconds=7*24*60*60)
			debugPrint('	Checking last seen date: Last seen {}, which is {} ago.'.format(device['lastSeen'],lastSeenDiff))
			if lastSeenDiff >= checkPeriod:
				debugPrint('	Device has been last seen longer than a week ago. Ignoring.')
				continue
		debugPrint("	Don't ignore.")
		# TODO: check if IP and MAC match
		# first get IP from MAC
		macIp = getIpFromMac(device['mac'])
		if macIp == False:
			# look if IP is assigned to someone else
			debugPrint("X Device {} with MAC {} has no IP in ARP cache.".format(readableNameOf(device),device['mac']))
			# if we know an IP of the device
			# TODO? get IP from table info
			if 'ip' in device.keys():
				currentOwner = getMacFromArp(device['ip'])
				if currentOwner != False:
					debugPrint("X! Its IP {} is currenly owned by {}. Ignoring.".format(device['ip'],readableNameOf({'mac': currentOwner, 'name': currentOwner})))
					continue
				else:
					#print("XX The IP {} of {} is currenly not owned by anyone. Pinging.".format(device['ip'],readableNameOf(device)))
					pingIp(device['ip'],device)
		elif macIp != device['ip']:
			# mismatch between table IP and the one from the ARP cache. Should not happen
			debugPrint("! Ignoring device {} because its IP {} is not {} which is assigned to its MAC {}.".format(readableNameOf(device),device['ip'],macIp,device['mac']))
			continue
		if not 'ip' in device.keys():
			#print("! Device {} has no known IP. Ignoring.".format(readableNameOf(device)))
			continue
		# ping device
		futures.append(pingDeviceAsync(device))

	for i, future in enumerate(asyncio.as_completed(futures)):
		result = await future
		device = result[0]
		deviceMac = device['mac']
		pingResult = result[1]
		if pingResult:
			debugPrint("+ Host {} at {} appears to be up.".format(readableNameOf(device),device['ip']))
			cameOnlineCheck(device)
			devices[deviceMac]['lastSeen'] = datetime.datetime.now()
			devices[deviceMac]['lastState'] = 'up'
		else:
			debugPrint("+ Host {} appears to be down. Last seen {}.".format(readableNameOf(device),device['lastSeen']))
			wentOfflineCheck(device)
			devices[deviceMac]['lastState'] = 'down'
			devices[deviceMac]['lastOffline'] = datetime.datetime.now()

	mqttSendAllDevices(devices)
	storeDevicelist(devices)

asyncio.run(main())
