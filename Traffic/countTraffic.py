#!/usr/bin/env python
# log traffic on unix
import subprocess
import sqlite3 as sql
import datetime
import sys
sys.path.insert(0,'..')
import ConfigParser
import json

def getPathToDB(selfPath):
	return "{}/traffic.db".format(selfPath);

def trafficInBytes(selfPath):
	bytes = subprocess.Popen("{}/callIfconfig.sh".format(selfPath), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True).stdout.read().split();
	return bytes;

def uptimeInSeconds(selfPath):
	# get uptime in seconds
	uptime = int(subprocess.Popen("{}/getUptimeSeconds.sh".format(selfPath), stdout=subprocess.PIPE).stdout.read())
	print 'Uptime: ',uptime, 's'
	return uptime

def saveToDatabase(uptime, traffic, selfPath):
	con = None;
	try:
		con = sql.connect(getPathToDB(selfPath));
		cur = con.cursor();
		print 'Received bytes:',traffic[0],', Transmitted bytes:',traffic[1];
		# get last entry
		cur.execute('SELECT * FROM traffic WHERE date = (SELECT MAX(date) FROM traffic)');
		data = cur.fetchone()
		print(data)

		if not data is None:
			print "Last entry from date ",datetime.datetime.fromtimestamp(data[0]),", total uptime ",uptime," vs. ",data[3];
		# no entry found or traffic is smaller than on last record, make new entry
		if data is None or int(traffic[0])<int(data[4]):
			print 'New entry made.';
			#emtpy database
			if data is None:
				cur.execute("INSERT INTO traffic VALUES (?,?,?,?,?,?)", (datetime.datetime.utcnow().strftime("%s"), traffic[0], traffic[1], uptime, traffic[0], traffic[1]));
			#rollover
			elif int(traffic[0])<int(data[4]):
				print "Rollover";
				diffUptime = int(datetime.datetime.utcnow().strftime("%s"))-int(data[0])
				cur.execute("INSERT INTO traffic VALUES (?,?,?,?,?,?)", (datetime.datetime.utcnow().strftime("%s"), traffic[0], traffic[1], diffUptime, traffic[0], traffic[1]));
		# if greater => same computer run and no overflow, calculate difference and make new record
		else:
			diffTraffic0 = int(traffic[0])-int(data[4])
			if diffTraffic0 < 0:
				print('Set trafficRX to 0 because it was '+str(diffTraffic0));
				diffTraffic0 = 0;

			diffTraffic1 = int(traffic[1])-int(data[5])
			if diffTraffic1 < 0:
				print('Set trafficTX to 0 because it was '+str(diffTraffic1));
				diffTraffic1 = 0;

			diffUptime = int(datetime.datetime.utcnow().strftime("%s"))-int(data[0])
			print "Make new entry with diff RX", diffTraffic0,", total RX", traffic[0],", diff TX", diffTraffic1,", total TX", traffic[1], " and diffUptime", diffUptime, "."
			cur.execute("INSERT INTO traffic VALUES (?,?,?,?,?,?)", (datetime.datetime.utcnow().strftime("%s"), diffTraffic0, diffTraffic1, diffUptime, traffic[0], traffic[1]));
		con.commit();

	except sql.Error, e:
		print "Error %s:" % e.args[0];

	finally:
		if con:
			con.close();

if __name__ == '__main__':
	config = ConfigParser.ConfigParser()
	config.read('config.ini')
	selfPath = config.get("Paths", "selfPath")

	uptime = uptimeInSeconds(selfPath);
	traffic = trafficInBytes(selfPath);
	saveToDatabase(uptime, traffic,selfPath);
	mqttObject = {
		"topic": "traffic",
		"measurements": {
			"uptime": uptime,
			"trafficReceived": traffic[0],
			"trafficTransmitted": traffic[1]
		}
	}
	json = json.dumps(mqttObject)
	print("Writing JSON: {}".format(json))
	sender = subprocess.Popen([config.get("Paths", "mqttPath")], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
	sender.stdin.write(json.encode('utf-8'))

