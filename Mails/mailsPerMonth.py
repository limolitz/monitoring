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
import pickle
import sys

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
	g('set title "Mails Received And Sent From '+data[0][0].strftime('%Y')+' to 2015"')
	g('set grid')
	g('set grid mxtics')
	filename = "mailsPerMonth_" + str(data[0][0].year)+ ".png"
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
	plot5 = Gnuplot.PlotItems.Data(formatted, using="($1):($3+$4) smooth bezier", title="Received, smoothed")
	plot6 = Gnuplot.PlotItems.Data(formatted, using="($1):($2) smooth bezier", title="Sent, smoothed")
	
	g.plot(plot1, plot2, plot3, plot4, plot5, plot6)
	print filename+" produced."


if __name__ == '__main__':
	if len(sys.argv) > 2 or len(sys.argv) < 1:
		print "Usage: python mailsPerDay.py"
		print "              mailsPerDay.py startYear"
		exit()
	login();
	data = []

	dateRange = [];
	# plot current year
	if len(sys.argv) == 1:
		for month in range(1, date.today().month+1):
			dateRange.append(datetime.date(date.today().year, month, 1))
	# plot from startYear to current year
	elif len(sys.argv) == 2:
		startYear = int(sys.argv[1])
		for year in range(startYear,date.today().year+1):
			if year == date.today().year:
				for month in range(1, date.today().month+1):
					dateRange.append(datetime.date(year, month, 1))
			else:
				for month in range(1, 13):
					dateRange.append(datetime.date(year, month, 1))

	for firstOfMonth in dateRange:
		sentNum = countSent(firstOfMonth);
		receivedNum = countReceived(firstOfMonth);

		data.append([firstOfMonth, firstOfMonth.strftime("%s"), sentNum, receivedNum])
	plot(data)
