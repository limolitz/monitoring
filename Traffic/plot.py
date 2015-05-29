#!/usr/bin/env python
import sqlite3 as sql
import datetime

import Gnuplot
import sys
import subprocess


def getPathToDB():
	return '/home/florin/bin/QuantifiedSelf/Traffic/traffic.db'

def plot():
	con = None
	try:
		# plot current month per default
		# read params
		if len(sys.argv) > 3 or len(sys.argv) < 1:
			print "Usage: python bankClient.py beginTimeStamp endTimestamp"
			print "              bankClient.py lastNDays"
			print "              bankClient.py"
			exit()
		#else:
		#	print(len(sys.argv))
		
		tic = ""
		title = "Traffic"
		if len(sys.argv) == 3:
			begin = datetime.datetime.fromtimestamp(int(sys.argv[1])) # start
			end = datetime.datetime.fromtimestamp(int(sys.argv[2])) # end
			tic=str(60*60*24*0.02)
		elif len(sys.argv) == 2:
			begin = datetime.datetime.today()-datetime.timedelta(days=int(sys.argv[1]))
			end = datetime.datetime.today() # end
			# tic
			tic=str(60*60*24*2)
			title = "Traffic last "+sys.argv[1]+" days"
		else:
			title = "Traffic this month"
			begin = datetime.date(datetime.datetime.today().year, datetime.datetime.today().month, 1)
			end = datetime.date(datetime.datetime.today().year, datetime.datetime.today().month+1, 1)-datetime.timedelta(1) # end
			tic = str(60*60*24*2)
		
		title = title+" as per "+datetime.datetime.today().strftime("%d.%m.%Y, %H:%M")+" UTC"
		print("Begin: "+str(begin))
		print("End: "+str(end))
		con = sql.connect(getPathToDB())
		cur = con.cursor()
		print('SELECT date, trafficRX, trafficTX, uptime FROM traffic WHERE date > '+begin.strftime("%s")+' AND date < '+end.strftime("%s")+' ORDER BY date')
		cur.execute('SELECT date, trafficRX, trafficTX, uptime FROM traffic WHERE date > '+begin.strftime("%s")+' AND date < '+end.strftime("%s")+' ORDER BY date');
		data = cur.fetchall();
		#print(data)
		adjustedData = []
		lastTX = 0;
		lastRX = 0;
		dataFile = open("traffic.data", "w")
		for date in data:
			adjustedDate = []
			adjustedDate.append(date[0])
			lastRX = date[1]+lastRX
			adjustedDate.append(lastRX)
			lastTX = date[2]+lastTX
			adjustedDate.append(lastTX)
			adjustedDate.append(date[3])
			adjustedData.append(adjustedDate)
			dataFile.write(str(date[0])+"	"+str(lastRX)+"	"+str(lastTX)+"	"+str(date[3])+"\n")
		dataFile.close()
		
		
		# build overall traffic counter
		counter = 0;
		overallTraffic = [];
		for index in range(len(data)):
			counter += data[index][1]+data[index][2];
			overallTraffic.append((data[index][0]+data[index][3]/2, counter));

		g = Gnuplot.Gnuplot()
		g('set term png truecolor size 700,400 font "Helvetica, 13pt" ')
		g('set output "traffic.png"')
		g('set title "'+title+' on ".system("uname -n")')
		g('set grid')
		g('set grid mxtics')
		g('set style data boxes')
		g('set style fill solid 0.7')

		g('set xdata time')
		# parse timestamp
		g('set timefmt "%s"')
		# set ad day-month
		g('set format x "%d.%m."')		
		# tic with 1 day
		#print('Tic: '+tic)
		g('set xtic '+tic)
		g('set xlabel "Date (UTC)"')
		g('set autoscale x')

		# tic width 4 GiB
		g('set ytic 8')
		g('set ylabel "Traffic (GiB)"')
		g('set yrange [0:]')

		g('set key center bottom outside horizontal')

		# Plot bytes in GiB (divide by 1024^3)
		plot1 = Gnuplot.PlotItems.File("traffic.data", using="($1-($4/2)):($2/1024**3):4", title="Received")
		plot2 = Gnuplot.PlotItems.File("traffic.data", using="($1-($4/2)):(($2+$3)/1024**3):4", title="Transmitted")		

		g.plot(plot2, plot1)#, plot3)

	except sql.Error, e:
		print "Error %s:" % e.args[0]
		#sys.exit(1)

	finally:
		if con:
			con.close()

if __name__ == '__main__':
	plot()
