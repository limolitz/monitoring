#!/usr/bin/env python
# Based loosely on https://github.com/danielstutzman/quantified-self/blob/master/count-things.rb
import imaplib
import time
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
	imap.debug = 0;


def countSent(day):
	global imap
	imap.select('Gesendet', True);
	today = day.strftime('%d-%b-%Y')

	tomorrow = (day + timedelta(days=+1)).strftime('%d-%b-%Y')


	search = imap.search(None, "BEFORE", tomorrow, "SINCE", today)
	if search[1][0]:
		sentMails = len(search[1][0].split(" "));
	else:
		sentMails = 0

	return sentMails

def countReceived(day):
	global imap
	imap.select('Archive', True);
	today = day.strftime('%d-%b-%Y');
	tomorrow = (day + timedelta(days=+1)).strftime('%d-%b-%Y');

	search = imap.search(None, "BEFORE", tomorrow, "SINCE", today);
	receivedArchive = len(search[1][0].split(" "));

	imap.select('INBOX', True);
	search = imap.search(None, "BEFORE", tomorrow, "SINCE", today);
	receivedInbox = len(search[1][0].split(" "));

	imap.select('Trash', True);
	search = imap.search(None, "BEFORE", tomorrow, "SINCE", today);
	receivedTrash = len(search[1][0].split(" "));

	receivedMails = receivedArchive + receivedInbox + receivedTrash;

	return receivedMails

def plot(data):
		g = Gnuplot.Gnuplot(persist=1)
		g('set term png truecolor size 1000,500 font "Helvetica, 13pt" ')
		g('set title "Mails Received And Sent In '+data[0][0].strftime('%B %Y')+'"')
		g('set grid')
		g('set grid mxtics')
		filename = "mails_" + str(data[0][0].month) + str(data[0][0].year)+ ".png"
		g('set output "'+filename+'"')

		g('set xdata time')

		# parse timestamp
		g('set timefmt "%s"')

		# set ad day-month
		g('set format x "%d.%m."')

		# tic with 1 day
		g('set xtic '+str(60*60*24*1))
		g('set xlabel "Date"')
		g('set autoscale x')

		g('set ytic 5')
		g('set ylabel "# of Mails"')
		g('set yrange [0:]')

		#g('set y2tic 4')
		#g('set autoscale y2')
		#g('set y2label "Received Mails"')
		#g('set y2range [0:]')

		g('set key center bottom outside horizontal')

		g('set style fill solid 1.0')
		g('set style data boxes')

		formatted = []
		for elem in data:
			formatted.append([elem[1], elem[2], elem[3]])

		plot1 = Gnuplot.PlotItems.Data(formatted, using="($1-60*60*5):($2):(60*60*8)", title="Sent")
		plot2 = Gnuplot.PlotItems.Data(formatted, using="($1+60*60*5):($3):(60*60*8)", title="Received")

		g.plot(plot1, plot2)


if __name__ == '__main__':
	login();
	data = []
	for day in range(1, date.today().day):
	#for day in range(1, 4):
		currentDate = datetime.date(date.today().year, date.today().month, day)

		sentNum = countSent(currentDate);
		receivedNum = countReceived(currentDate);

		data.append([currentDate, currentDate.strftime("%s"), sentNum, receivedNum])

	plot(data)
