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
		cur.execute('SELECT date, trafficRX, trafficTX FROM traffic');
		data = cur.fetchall();

		# TODO(wasmitnetzen): map all entries from same date to one entry
		#print map(lambda x: [x[0], (x[1]/1024)], data);
		#print data

		g = Gnuplot.Gnuplot(persist=1)
		g('set term png truecolor size 1000,500 font "Helvetica, 13pt" ')
		g('set output "traffic.png"')
		g('set title "Traffic per day"')
		g('set grid')
		g('set grid mxtics')
		g('set style data boxes')
		g('set boxwidth 0.8 relative')
		g('set style fill solid 0.7')


		g('set xdata time')
		g('set timefmt "%s"')
		g('set format x "%d.%m"')
		g('set xtic '+str(60*60*24*1))
		g('set xlabel "Date"')
		g('set autoscale x')

		g('set ytic 1024')
		g('set ylabel "Traffic (MiB)"')
		g('set yrange [0:]')

		plot = Gnuplot.PlotItems.Data(data, using="1:($2/1024**2)")

		g.plot(plot)
		#raw_input('Please press return to continue...\n')
		#gplt.output(plotfile,'png medium transparent picsize 600 400')

	except sql.Error, e:
		print "Error %s:" % e.args[0]
		#sys.exit(1)

	finally:
		if con:
			con.close()

if __name__ == '__main__':
	plot()
