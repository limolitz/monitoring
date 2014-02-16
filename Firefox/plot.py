import sqlite3 as sql
import datetime
import Gnuplot


def getPathToDB():
  return '/home/florin/bin/QuantifiedSelf/Firefox/firefoxProcesses.db'

def prettyDate(data):
  #print data;
  #dataNew = datetime.datetime.fromtimestamp(data[0]).strftime('%Y-%m-%d');
  dataNew = datetime.datetime.fromtimestamp(data[0]).strftime('%y%m%d');
  return [dataNew, data[1]];

def plot():
        con = None
        try:
                con = sql.connect(getPathToDB())
                cur = con.cursor()
                cur.execute('SELECT date, tabs FROM tabNumber WHERE profile = "standard"');
                data = cur.fetchall();
                
                data = map(prettyDate, data);
                #prettyDate(data[[1,1]]);
                
                
                #print data;
                #TODO(wasMitNetzen): construct actual plot points with date and value
                
                g = Gnuplot.Gnuplot(persist=1)
                g('set term png truecolor size 1000,500 font "Helvetica, 13pt" ')
                g('set title "Development of opened Firefox tabs over time"')
                g('set grid')
		g('set grid mxtics')
                g('set output "tabs.png"')
                #g('set xtic '+str(60*60*24*7))
                g('set xtic 1')
		g('set xlabel "Date (s)"')
		g('set ylabel "# of opened Firefox tabs"')		
		g('set style fill solid 1.0')
		g('set style data boxes')
		g.plot(data)
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
