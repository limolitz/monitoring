#!/usr/bin/env python
# log traffic on unix
import subprocess
import sqlite3 as sql
import datetime
import sys
sys.path.insert(0,'..')
import mqttsend

def getPathToDB():
	return '/home/florin/bin/QuantifiedSelf/Traffic/traffic.db';

def trafficInBytes():
	bytes = subprocess.Popen('/home/florin/bin/QuantifiedSelf/Traffic/callIfconfig.sh', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True).stdout.read().split();
	#print bytes
	return bytes;

def uptimeInSeconds():
	# get uptime in seconds
	uptime = int(subprocess.Popen('/home/florin/bin/QuantifiedSelf/Traffic/getUptimeSeconds.sh', stdout=subprocess.PIPE).stdout.read())
	print 'Uptime: ',uptime, 's'
	return uptime

def saveToDatabase(uptime, traffic):
	con = None;
	try:
		con = sql.connect(getPathToDB());
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
	uptime = uptimeInSeconds();
	traffic = trafficInBytes();
	saveToDatabase(uptime, traffic);
	data = {}
	data["timestamp"] = datetime.datetime.utcnow().strftime("%s")
	data["uptime"] = uptime
	data["trafficReceived"] = traffic[0]
	data["trafficTransmitted"] = traffic[1]
	mqttsend.sendMQTT("traffic", data);
