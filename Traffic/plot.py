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
		cur.execute('SELECT date, trafficRX, trafficTX, uptime FROM traffic');
		data = cur.fetchall();

		g = Gnuplot.Gnuplot(persist=1)
		g('set term png truecolor size 1000,500 font "Helvetica, 13pt" ')
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
		g('set format x "%d.%m %H:%M"')
		# tic with 1 day
		g('set xtic '+str(60*60*24*0.5))
		g('set xlabel "Date"')
		g('set autoscale x')

		# tic width 1 GiB
		g('set ytic 1024')
		g('set ylabel "Traffic (MiB)"')
		g('set yrange [0:]')

		# Plot bytes in MiB (divide by 1024^2)
		plot1 = Gnuplot.PlotItems.Data(data, using="1:($2/1024**2):4", title="Received")
		plot2 = Gnuplot.PlotItems.Data(data, using="1:(($2+$3)/1024**2):4", title="Transmitted")

		g.plot(plot2, plot1)

	except sql.Error, e:
		print "Error %s:" % e.args[0]
		#sys.exit(1)

	finally:
		if con:
			con.close()

if __name__ == '__main__':
	plot()
