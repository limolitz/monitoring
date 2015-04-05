#!/usr/bin/env python
# Based loosely on https://github.com/danielstutzman/quantified-self/blob/master/count-things.rb
import imaplib
import time
import calendar
import datetime
from datetime import date
from datetime import timedelta
import Gnuplot
import ConfigParser

def login():
	config = ConfigParser.ConfigParser()
	config.read("config.ini")

	global imap
	imap = imaplib.IMAP4_SSL(config.get("Account", "server"), config.get("Account", "port"))
	imap.login(config.get("Account", "user"),config.get("Account", "password"))
	imap.debug = 1;


def countSent(firstOfMonth):
	global imap
	imap.select('Gesendet', True);
	
	firstOfMonthString = firstOfMonth.strftime('%d-%b-%Y');
	
	endOfMonth = datetime.date(firstOfMonth.year, firstOfMonth.month, calendar.monthrange(firstOfMonth.year, firstOfMonth.month)[1]);
	endOfMonthString = endOfMonth.strftime('%d-%b-%Y');	

	search = imap.search(None, "BEFORE", endOfMonthString, "SINCE", firstOfMonthString)
	sentMails = 0 if search[1][0] == "" else len(search[1][0].split(" "));

	return sentMails

def countReceived(firstOfMonth):
	global imap
	
	firstOfMonthString = firstOfMonth.strftime('%d-%b-%Y');
	
	endOfMonth = datetime.date(firstOfMonth.year, firstOfMonth.month, calendar.monthrange(firstOfMonth.year, firstOfMonth.month)[1]);
	endOfMonthString = endOfMonth.strftime('%d-%b-%Y');	
	
	# select Archive
	imap.select('Archive', True);
	# search for mails between firstOfMonthString and endOfMonthString
	search = imap.search(None, "BEFORE", endOfMonthString, "SINCE", firstOfMonthString);
	receivedArchive = 0 if search[1][0] == "" else len(search[1][0].split(" "));

	imap.select('INBOX', True);
	search = imap.search(None, "BEFORE", endOfMonthString, "SINCE", firstOfMonthString);
	receivedInbox = 0 if search[1][0] == "" else len(search[1][0].split(" "));
	
	imap.select('Uni', True);
	search = imap.search(None, "BEFORE", endOfMonthString, "SINCE", firstOfMonthString);
	receivedUni = 0 if search[1][0] == "" else len(search[1][0].split(" "));

	imap.select('Trash', True);
	search = imap.search(None, "BEFORE", endOfMonthString, "SINCE", firstOfMonthString);
	receivedTrash = 0 if search[1][0] == "" else len(search[1][0].split(" "));
		
	return (receivedArchive, receivedInbox+receivedUni, receivedTrash);

def plot(data):
	g = Gnuplot.Gnuplot(persist=1)
	g('set term png truecolor size 1000,500 font "Helvetica, 13pt" ')
	g('set title "Mails Received And Sent In '+data[0][0].strftime('%Y')+'"')
	g('set grid')
	g('set grid mxtics')
	filename = "mails_" + str(data[0][0].year)+ ".png"
	g('set output "'+filename+'"')

	# set input data as time
	g('set xdata time')

	# set that input data is a timestamp
	g('set timefmt "%s"')

	# set output format as month.
	g('set format x "%m."')

	# tic with 1 month
	g('set xtic 2592000')
	g('set autoscale x')
	
	g('set xlabel "Month"')

	g('set ytic 50')
	g('set ylabel "# of Mails"')
	g('set yrange [0:]')

	g('set key center bottom outside horizontal')

	g('set style fill solid 1.0')
	g('set style data boxes')

	formatted = []
	for elem in data:
		formatted.append([elem[1], elem[2], elem[3][0], elem[3][1], elem[3][2]])
		
	# data:
	#  $1: date
	#  $2: sent
	#  $3: Received, archived
	#  $4: Received, inbox
	#  $5, Received, deleted

	plot1 = Gnuplot.PlotItems.Data(formatted, using="($1-60*60*24*6):($2):(60*60*24*12)", title="Sent")
	plot2 = Gnuplot.PlotItems.Data(formatted, using="($1+60*60*24*6):($3+$4+$5):(60*60*24*12)", title="Received, deleted")
	plot3 = Gnuplot.PlotItems.Data(formatted, using="($1+60*60*24*6):($3+$4):(60*60*24*12)", title="Received, Inbox")
	plot4 = Gnuplot.PlotItems.Data(formatted, using="($1+60*60*24*6):($3):(60*60*24*12)", title="Received, archived")

	g.plot(plot1, plot2, plot3, plot4)


if __name__ == '__main__':
	login();
	data = []
	#for month in range(1, date.today().month+1):
	for month in range(1, 13):	
		#firstOfMonth = datetime.date(date.today().year, month, 1)
		firstOfMonth = datetime.date(2014, month, 1)

		sentNum = countSent(firstOfMonth);
		receivedNum = countReceived(firstOfMonth);

		data.append([firstOfMonth, firstOfMonth.strftime("%s"), sentNum, receivedNum])

	plot(data)
