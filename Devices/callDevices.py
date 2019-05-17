#!/usr/bin/env python3.7
# -*- coding: UTF-8 -*-

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
import http.client
import http.cookiejar
import asyncio
import sys

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

def readableNameOf(device,quiet=False):
	name = readableNameMac(device['mac'])
	if name is not False:
		return name
	else:
		if not(quiet):
			debugPrint("	No readable name of {} known. Use self-given name {}.".format(device['mac'],device['name']))
		return device['name']

def readableNameMac(mac):
	config = configparser.ConfigParser(delimiters='=')
	config.read('config.ini')
	if not isinstance(mac, str):
		print("Given mac {} is not a string: {}.".format(mac,type(mac)))
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
			hours = int(minutes / 60)
			minutes = minutes - hours * 60
		else:
			return "{:02}min".format(minutes)
		if hours >= 24:
			days = int(hours / 24)
			hours = hours - days * 24
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
		sender = await asyncio.create_subprocess_exec("/bin/ping", "-qc", "1", "-W", "3", ip, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
		output, errors = await sender.communicate()
		if len(errors) > 0:
			print(output.decode("utf-8"),file=sys.stderr)
			print(errors.decode("utf-8"),file=sys.stderr)
		if sender.returncode == 0:
			if i != 0:
				debugPrint("{}. Ping to {} ({}) successfull.".format(i,readableNameOf(device['mac'],True),ip))
			return True
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
				debugPrint("{}. Ping to {} ({}) successfull.".format(i,readableNameOf(device['mac'],True),ip))
			return True
	return False

def sshTestDevice(ip):
	return os.system("ssh '{}' true > /dev/null".format(ip)) == 0

def getMacFromArp(ip):
	line = subprocess.Popen("/usr/sbin/arp -an | grep '{}' | grep -oP '[a-f\:0-9]{{17}}'".format(ip), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True).stdout.read().split()
	if len(line) > 0:
		return line[0].decode("utf-8").upper()
	else:
		debugPrint("Could not find a MAC for IP {}.".format(ip))
		return None

def getIpFromMac(mac):
	line = subprocess.Popen("/usr/sbin/arp -na | grep -i '{}' | awk '{{print $2}}' | cut -c 2- | rev | cut -c 2- | rev".format(mac), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True).stdout.read().split()
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
	# print(mqttDict)
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

	# mqttSend(mqttDict)

def mqttSend(jsonDict):
	config = configparser.ConfigParser(delimiters='=')
	config.read('config.ini')
	jsonData = json.dumps(jsonDict)
	# debugPrint("Writing JSON: {}".format(jsonData))
	sender = subprocess.Popen([config.get("Paths", "mqttPath")], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
	output, errors = sender.communicate(jsonData.encode("utf-8"))
	# debugPrint("Output: {}, errors: {}".format(output,errors))

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
	if 'lastState' in device:
		if device['lastState'] != 'up':
			if device['lastSeen'] is not None:
				timeDifference = datetime.datetime.utcnow() - device['lastSeen']
				message = "{} ⇑. Last seen {} ({} ago).".format(readableNameOf(device),formatTime(device['lastSeen']),formatTimedifference(timeDifference))

			else:
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
	if 'lastState' in device:
		if device['lastState'] != 'down':
			if device['lastOffline'] is not None and isinstance(device['lastOffline'],datetime.datetime):
				timeDifference = datetime.datetime.utcnow() - device['lastOffline']
				message = "{} ⇓. Online since {} ({} ago).".format(readableNameOf(device), formatTime(device['lastOffline']), formatTimedifference(timeDifference))
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
	soup = BeautifulSoup(line, 'lxml-xml')
	for host in soup.find_all('host'):
		ip = host.find('address')['addr']
		if host.find('hostname') is not None:
			hostname = host.find('hostname')['name']
		mac = getMacFromArp(ip)
		# fix own MAC which can't be found in arp table
		if mac is None and hostname == "frost.lan":
			mac = 'B8:27:EB:4A:D9:5E'
		# still no mac, we can't store the info about the device, so we ignore it
		if mac is None:
			print("No MAC for host {} from nmap, ignoring.".format(host))
			continue
		if readableNameMac(mac) is not False:
			hostname = readableNameMac(mac)
		if mac is not None and hostname is not None and not(isinstance(mac, bool)):
			debugPrint("Hostname {}, MAC {}, IP {}.".format(hostname, mac, ip))
			clients.append({'name': hostname, 'mac': mac, 'ip': ip})
		else:
			print("Mac or Hostname is none or bool for {},{} at IP {}.".format(mac, hostname, ip))
	return clients

async def main():
	devices = loadDevicelist()
	clientsList = loadDevicesFromNmap()

	futures = []
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
		device = devices[deviceMac]
		if deviceMac == "":
			print("Ignoring device {} because its MAC is empty.".format(device),file=sys.stderr)
			continue
		if deviceMac is None:
			print("Ignoring device {} because its MAC is None.".format(device),file=sys.stderr)
			continue
		if isinstance(deviceMac, bool):
			print("Ignoring device {} because its MAC is {}.".format(device, deviceMac),file=sys.stderr)
			continue
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
			checkPeriod = datetime.timedelta(seconds=7 * 24 * 60 * 60)
			debugPrint('	Checking last seen date: Last seen {}, which is {} ago.'.format(device['lastSeen'],lastSeenDiff))
			if lastSeenDiff >= checkPeriod:
				debugPrint('	Device has been last seen longer than a week ago. Ignoring.')
				continue
		debugPrint("	Don't ignore.")
		# TODO: check if IP and MAC match
		# first get IP from MAC
		macIp = getIpFromMac(device['mac'])
		if macIp is False:
			# look if IP is assigned to someone else
			debugPrint("X Device {} with MAC {} has no IP in ARP cache.".format(readableNameOf(device),device['mac']))
			# if we know an IP of the device
			# TODO: get IP from table info?
			if 'ip' in device.keys():
				currentOwner = getMacFromArp(device['ip'])
				if currentOwner is not None:
					debugPrint("X! Its IP {} is currenly owned by {}. Ignoring.".format(device['ip'],readableNameOf({'mac': currentOwner, 'name': currentOwner})))
					continue
		elif macIp != device['ip']:
			# mismatch between table IP and the one from the ARP cache. Should not happen
			debugPrint("! Ignoring device {} because its IP {} is not {} which is assigned to its MAC {}.".format(readableNameOf(device),device['ip'],macIp,device['mac']))
			continue
		if 'ip' not in device.keys():
			debugPrint("! Device {} has no known IP. Ignoring.".format(readableNameOf(device)))
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
	if False in devices.keys():
		print("Deleting device with MAC False: {}".format(devices[False]),file=sys.stderr)
		del(devices[False])
	storeDevicelist(devices)

asyncio.run(main())
