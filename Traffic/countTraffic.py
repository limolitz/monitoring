#!/usr/bin/env python3
# log traffic on unix
import subprocess
import sqlite3 as sql
import datetime
import sys
sys.path.insert(0,'..')
import configparser
import json

def getPathToDB(selfPath):
	return "{}/traffic.db".format(selfPath)

def trafficInBytes(selfPath):
	bytes = subprocess.Popen("{}/callIfconfig.sh".format(selfPath), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True).stdout.read().split()
	return bytes

def uptimeInSeconds(selfPath):
	# get uptime in seconds
	uptime = int(subprocess.Popen("{}/getUptimeSeconds.sh".format(selfPath), stdout=subprocess.PIPE).stdout.read())
	print('Uptime: {}s'.format(uptime))
	return uptime

def saveToDatabase(uptime, traffic, selfPath):
	con = None
	try:
		con = sql.connect(getPathToDB(selfPath))
		cur = con.cursor()
		receivedBytesOld=int(traffic[0])
		transmittedBytesOld=int(traffic[1])
		print('Received bytes: {}, Transmitted bytes: {}'.format(receivedBytesOld,transmittedBytesOld))
		# get last entry
		cur.execute('SELECT * FROM traffic WHERE date = (SELECT MAX(date) FROM traffic)')
		data = cur.fetchone()
		print("Old data: {}".format(data))

		if not data is None:
			print("Last entry from date {}, total uptime {} vs . {}.".format(datetime.datetime.fromtimestamp(data[0]),uptime,data[3]))
		# no entry found or traffic is smaller than on last record, make new entry
		if data is None or int(receivedBytesOld)<int(data[4]):
			print('New entry made.')
			#emtpy database
			if data is None:
				cur.execute("INSERT INTO traffic VALUES (?,?,?,?,?,?)", (datetime.datetime.utcnow().strftime("%s"), receivedBytesOld, transmittedBytesOld, uptime, receivedBytesOld, transmittedBytesOld))
			#rollover
			elif int(receivedBytesOld)<int(data[4]):
				print("Rollover")
				diffUptime = int(datetime.datetime.utcnow().strftime("%s"))-int(data[0])
				cur.execute("INSERT INTO traffic VALUES (?,?,?,?,?,?)", (datetime.datetime.utcnow().strftime("%s"), receivedBytesOld, transmittedBytesOld, diffUptime, receivedBytesOld, transmittedBytesOld))
		# if greater => same computer run and no overflow, calculate difference and make new record
		else:
			diffTraffic0 = int(receivedBytesOld)-int(data[4])
			if diffTraffic0 < 0:
				print('Set trafficRX to 0 because it was '+str(diffTraffic0))
				diffTraffic0 = 0

			diffTraffic1 = int(transmittedBytesOld)-int(data[5])
			if diffTraffic1 < 0:
				print('Set trafficTX to 0 because it was '+str(diffTraffic1))
				diffTraffic1 = 0

			diffUptime = int(datetime.datetime.utcnow().strftime("%s"))-int(data[0])
			print("Make new entry with diff RX {}, total RX {}, diff TX {}, total TX {} and diffUptime {}.".format(diffTraffic0,receivedBytesOld,diffTraffic1,transmittedBytesOld,diffUptime))
			cur.execute("INSERT INTO traffic VALUES (?,?,?,?,?,?)", (datetime.datetime.utcnow().strftime("%s"), diffTraffic0, diffTraffic1, diffUptime, receivedBytesOld, transmittedBytesOld))
		con.commit()

	except sql.Error as e:
		print("Error {}.".format(e.args[0]))

	finally:
		if con:
			con.close()

if __name__ == '__main__':
	config = configparser.ConfigParser()
	config.read('config.ini')
	selfPath = config.get("Paths", "selfPath")

	uptime = uptimeInSeconds(selfPath)
	traffic = trafficInBytes(selfPath)
	saveToDatabase(uptime, traffic, selfPath)
	mqttObject = {
		"topic": "traffic",
		"measurements": {
			"uptime": uptime,
			"trafficReceived": int(traffic[0]),
			"trafficTransmitted": int(traffic[1])
		}
	}
	json = json.dumps(mqttObject)
	print("Writing JSON: {}".format(json))
	sender = subprocess.Popen([config.get("Paths", "mqttPath")], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
	sender.stdin.write(json.encode('utf-8'))

