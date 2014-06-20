# log traffic on unix
import subprocess
import sqlite3 as sql
import datetime

def getPathToDB():
	return '/home/florin/bin/QuantifiedSelf/Traffic/traffic.db'

def trafficInBytes():
	bytes = subprocess.Popen('/home/florin/bin/QuantifiedSelf/Traffic/callIfconfig.sh', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True,).stdout.read().split();
	#print bytes
	return bytes

def uptimeInSeconds():
	# get uptime in seconds
	uptime = int(subprocess.Popen('/home/florin/bin/QuantifiedSelf/Traffic/getUptimeSeconds.sh', stdout=subprocess.PIPE).stdout.read())
	print 'Uptime: ',uptime, 's'
	return uptime

def saveToDatabase():
	con = None;
	try:
		con = sql.connect(getPathToDB());
		cur = con.cursor();
		uptime = uptimeInSeconds();
		traffic = trafficInBytes();
		print 'Recevied bytes:',traffic[0],', Transmitted bytes:',traffic[1];
		# get last entry
		cur.execute('SELECT * FROM traffic WHERE date = (SELECT MAX(date) FROM traffic)');
		data = cur.fetchone()
		print(data)

		if not data is None:
			print "Last entry from date ",data[0],", uptime ",uptime," vs. ",data[3];
		# no entry found or traffic is smaller than on last record, make new entry
		if data is None or traffic[0]<data[4]:
			print('New entry made.')
			cur.execute("INSERT INTO traffic VALUES (?,?,?,?,?,?)", (datetime.datetime.utcnow().strftime("%s"), traffic[0], traffic[1], uptime, traffic[0], traffic[1]));
		# if greater => same computer run, calculate difference and make new record
		else:
			diffTraffic0 = int(traffic[0])-int(data[4])
			diffTraffic1 = int(traffic[1])-int(data[5])
			diffUptime = int(datetime.datetime.utcnow().strftime("%s"))-int(data[0])
			print("Make new entry with RX "+str(diffTraffic0)+", TX "+str(diffTraffic1)+" and diffUptime "+str(diffUptime)+".")
			cur.execute("INSERT INTO traffic VALUES (?,?,?,?,?,?)", (datetime.datetime.utcnow().strftime("%s"), diffTraffic0, diffTraffic1, diffUptime, traffic[0], traffic[1]));
			#cur.execute("UPDATE traffic set uptime = ?, trafficRX=?, trafficTX=? where date=?",(uptime, traffic[0], traffic[1], data[0]));
		con.commit();

	except sql.Error, e:
		print "Error %s:" % e.args[0]

	finally:
		if con:
			con.close()


if __name__ == '__main__':
	saveToDatabase()
