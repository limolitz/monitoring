# log traffic on unix
import subprocess
import sqlite3 as sql
import datetime

def getPathToDB():
  return '/home/florin/bin/QuantifiedSelf/Traffic/traffic.db'

def trafficInBytes():
	bytes = subprocess.Popen('/home/florin/bin/QuantifiedSelf/Traffic/callIfconfig.sh', stdout=subprocess.PIPE).stdout.read().split();
	print bytes
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
                print 'RX:',traffic[0],', TX:',traffic[1];
                # get last entry
                cur.execute('SELECT * FROM traffic WHERE date = (SELECT MAX(date) FROM traffic)');
                data = cur.fetchone()
  
		print "Last entry from date ",data[0],", uptime ",data[3];
		# no entry found or uptime is smaller than on last record, make new entry
		if data is None or uptime < data[3]:
		    print('New entry made.')
		    cur.execute("INSERT INTO traffic VALUES (?,?,?,?)", (datetime.datetime.now().strftime("%s"), traffic[0], traffic[1], uptime));	    
		# if greater => same computer run, update last record
		elif uptime > data[3]:
		    cur.execute("UPDATE traffic set uptime = ?, trafficRX=?, trafficTX=? where date=?",(uptime, traffic[0], traffic[1], data[0]));
		    print 'Updated ',data[0],' to uptime ',data[3];
		else:
		  print 'Error'
		con.commit();
                #cur.execute("INSERT INTO traffic VALUES (?,?,?)", (datetime.datetime.now().strftime("%s"), 'standard', getOpenedFirefoxTabs('/home/florin/.mozilla/firefox/3wxc4x2q.default/sessionstore.js')))
                #con.commit()
                #cur.execute("UPDATE traffic (?,?,?)", (datetime.datetime.now().strftime("%s"), 'nova', getOpenedFirefoxTabs('/home/florin/Dropbox/Programme/Firefox/jys16p25.Nova-sync/sessionstore.js')))
                #con.commit()

        except sql.Error, e:
                print "Error %s:" % e.args[0]                

        finally:
                if con:
                        con.close()


if __name__ == '__main__':
        saveToDatabase()