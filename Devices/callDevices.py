#!/usr/bin/env python3
import http.client
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
			debugPrint("	No readable name of {} known. Use self-given name {}.".format(mac,device['name']))
		return device['name']

def readableNameMac(mac):
	config = configparser.ConfigParser(delimiters='=')
	config.read('config.ini')
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

def jsonifyDates(device,keys):
	for key in keys:
		if key in device:
			dateToFormat = device[key]
			if dateToFormat is not None:
				if isinstance(dateToFormat, datetime.datetime):
					device[key] = dateToFormat.strftime("%s")
				else:
					if key != 'expireTime':
						print("Unknown instance {} on key {}. Setting to none.".format(type(dateToFormat),key))
					device[key] = None
	return device

def sanitizeDevice(device,deviceMac):
	device['mac'] = deviceMac
	device['readableName'] = readableNameMac(deviceMac)
	if 'lastConnectDiff' in device.keys():
		del(device['lastConnectDiff'])
	device = jsonifyDates(device,['expireTime', 'lastOffline', 'lastSeen', 'lastConnect'])
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

def loadDevicesFromRouter():
	#http.client.HTTPConnection.debuglevel = 1

	devicelist = 'http://192.168.0.1/basic/dhcp.asp'
	loginPath = 'http://192.168.0.1/goform/login'
	systemPath = 'http://192.168.0.1/status/system.asp'
	logoutPath = 'http://192.168.0.1/logout.asp'

	response = urllib.request.urlopen(devicelist)
	html = response.read().decode('utf8')
	soup = BeautifulSoup(html, 'html.parser')
	#print(soup.prettify())
	# check if we are already logged in
	#print(soup.prettify())
	directValue = soup.find_all('div', attrs={'class': 'upc_grid_9'})
	if (len(directValue) != 1):

		CSRFForm = soup.find("form", attrs={"name": "login"}).find("input", attrs={"name": "CSRFValue"})
		CSRFValue = CSRFForm["value"]
		#print(CSRFValue)

		data = "CSRFValue={}&loginUsername=admin&loginPassword=admin&logoffUser=0".format(CSRFValue).encode()
		req = urllib.request.Request(loginPath, data=data)
		req.add_header('Referer', 'http://192.168.0.1/login.asp')
		#print(dir(req))
		response = urllib.request.urlopen(req)
		html = response.read().decode('utf8')

		#print(html)

		req = urllib.request.Request(devicelist)
		response = urllib.request.urlopen(req)
		html = response.read().decode('utf8')
		soup = BeautifulSoup(html, 'html.parser')
		#print(soup.prettify())
		directValue = soup.find_all('div', attrs={'class': 'upc_grid_9'})

	clients = []

	clientsTable = soup.find('div', attrs={'class': 'upc_grid_9'})
	#print(clientsTable.prettify())
	clientsEntry = clientsTable.find_all('tr')
	#print(clients)
	for client in clientsEntry:
		#print("Client: {}".format(client))
		cells = client.find_all('td')
		if (len(cells) == 6):
			name = cells[0].get_text()
			mac = cells[1].get_text()
			ip = cells[2].get_text()
			etherOrWifi = cells[3].get_text()
			RSSI = cells[4].get_text()
			expires = cells[5].get_text()
			try:
				expiresFormatted = datetime.datetime.strptime(expires, "%Y-%m-%d %H:%M:%S")
			except ValueError as e:
				debugPrint("Unexpected expire format: {}".format(expires))
				expiresFormatted = None
			clients.append({'name': name, 'network': etherOrWifi, 'mac': mac, 'ip': ip, 'expireTime': expiresFormatted})

	# log out
	response = urllib.request.urlopen(logoutPath)
	html = response.read().decode('utf8')

	return clients

#print("Caller: {}, manual call? {}".format(findCaller(),getIfManualCall()))

devices = loadDevicelist()
clientsList = loadDevicesFromRouter()

for client in clientsList:
	# divide infos
	#print(clientSplit)
	# name elements
	name = client['name']
	network = client['network']
	ip = client['ip']
	mac = client['mac']
	expireTime = client['expireTime']
	if not(expireTime is None):
		expiresIn = expireTime-datetime.datetime.now()
		# 25 hours?
		expireDelta = datetime.timedelta(seconds=86400+3600)

		lastConnectDiff = expiresIn-expireDelta
		lastConnect = expireTime-expireDelta
		debugPrint("- {} ({}) is on {} with the ip {} and the MAC {}, expire time: {} (which is in {}), last connect: {} (which is {} ago).".format(readableNameMac(mac),name,network,ip,mac,expireTime,expiresIn,lastConnect,-lastConnectDiff))
	else:
		lastConnectDiff = None
		lastConnect = None
		debugPrint("- {} ({}) is on {} with the ip {} and the MAC {}, expire time: {}.".format(readableNameMac(mac),name,network,ip,mac,expireTime))

	# build entry
	deviceInfo = {'name': name, 'network': network, 'mac': mac, 'ip': ip, 'expireTime': expireTime, 'lastConnectDiff': lastConnectDiff, 'lastConnect': lastConnect}

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
	if pingDevice(device):
		debugPrint("+ Host {} appears to be up.".format(readableNameOf(device)))
		cameOnlineCheck(device)
		devices[deviceMac]['lastSeen'] = datetime.datetime.now()
		devices[deviceMac]['lastState'] = 'up'
	else:
		#debugPrint("+ Host {} appears to be down. Last connect ~{} ago. Last seen {}.".format(readableNameOf(device),formatTimedifference(device['lastConnectDiff']),device['lastSeen']))
		wentOfflineCheck(device)
		devices[deviceMac]['lastState'] = 'down'
		devices[deviceMac]['lastOffline'] = datetime.datetime.now()

mqttSendAllDevices(devices)
storeDevicelist(devices)
