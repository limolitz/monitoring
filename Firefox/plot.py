import sqlite3 as sql
import datetime
import Gnuplot


def getPathToDB():
	return '/home/florin/bin/QuantifiedSelf/Firefox/firefoxProcesses.db'

def plot():
	con = None
	try:
		con = sql.connect(getPathToDB())
		cur = con.cursor()
		cur.execute('SELECT date, tabs FROM tabNumber WHERE profile = "standard"');
		data = cur.fetchall();

		g = Gnuplot.Gnuplot(persist=1)
		g('set term png truecolor size 1000,500 font "Helvetica, 13pt" ')
		g('set title "Development of opened Firefox tabs over time"')
		g('set grid')
		g('set grid mxtics')
		g('set output "tabs.png"')

		g('set xdata time')
		g('set timefmt "%s"')
		g('set format x "%d.%m"')
		g('set xtic '+str(60*60*24*3))
		g('set xlabel "Date"')

		g('set ylabel "# of opened Firefox tabs"')

		g('set style fill solid 1.0')
		g('set style data boxes')

		plot = Gnuplot.PlotItems.Data(data, using=(1,2))

		g.plot(plot)
		#g.plot(data, using="1:2")
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
