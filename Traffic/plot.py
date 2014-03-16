#!/usr/bin/env python
import sqlite3 as sql
import datetime
import Gnuplot


def getPathToDB():
	return '/home/florin/bin/QuantifiedSelf/Traffic/traffic.db'

def plot():
	con = None
	try:
		con = sql.connect(getPathToDB())
		cur = con.cursor()
		cur.execute('SELECT date, trafficRX, trafficTX, uptime FROM traffic ORDER BY date');
		data = cur.fetchall();

		# build overall traffic counter
		counter = 0;
		overallTraffic = [];
		for index in range(len(data)):
			counter += data[index][1]+data[index][2];
			overallTraffic.append((data[index][0]+data[index][3]/2, counter));
		#print data[1]
		#print datetime.datetime.utcfromtimestamp(data[0][0]);
		#delta = datetime.timedelta(0, int(data[0][3]));
		#print delta;
		#print datetime.datetime.utcfromtimestamp(data[0][0])+delta;

		#print overallTraffic;
		g = Gnuplot.Gnuplot(persist=1)
		g('set term png truecolor size 1000,750 font "Helvetica, 13pt" ')
		g('set output "traffic.png"')
		g('set title "Traffic per run"')
		g('set grid')
		g('set grid mxtics')
		g('set style data boxes')
		g('set style fill solid 0.7')


		g('set xdata time')
		# parse timestamp
		g('set timefmt "%s"')
		# set ad day-month
		g('set format x "%d.%m."')
		#g('set format x "%s"')
		# tic with 1 day
		g('set xtic '+str(60*60*24*1))
		g('set xlabel "Date (UTC)"')
		g('set autoscale x')

		# tic width 4 GiB
		g('set ytic 4')
		g('set ylabel "Traffic per run (GiB)"')
		g('set yrange [0:]')

		g('set y2tic 16')
		g('set autoscale y2')
		g('set y2label "Overall Traffic (GiB)"')
		g('set y2range [0:]')

		g('set key center bottom outside horizontal')

		# Plot bytes in MiB (divide by 1024^2)
		plot1 = Gnuplot.PlotItems.Data(data, using="($1+($4/2)):($2/1024**3):4", title="Received")
		plot2 = Gnuplot.PlotItems.Data(data, using="($1+($4/2)):(($2+$3)/1024**3):4", title="Transmitted")
		plot3 = Gnuplot.PlotItems.Data(overallTraffic, title="Overall Traffic", with_="steps", using="1:($2/1024**3)", axes="x1y2")

		g.plot(plot2, plot1, plot3)

	except sql.Error, e:
		print "Error %s:" % e.args[0]
		#sys.exit(1)

	finally:
		if con:
			con.close()

if __name__ == '__main__':
	plot()
