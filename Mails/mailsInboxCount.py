#!/usr/bin/env python3
# Based loosely on https://github.com/danielstutzman/quantified-self/blob/master/count-things.rb
import imaplib
import time
import datetime
import subprocess
import datetime
#import Gnuplot
import configparser
import email
import email.header
from statistics import mean


def login():
	config = configparser.ConfigParser()
	config.read("/home/florin/bin/QuantifiedSelf/Mails/config.ini")

	global imap
	imap = imaplib.IMAP4_SSL(config.get("Account", "server"), config.get("Account", "port"))
	imap.login(config.get("Account", "user"),config.get("Account", "password"))
	imap.debug = 0;

def countFolder(folder):
	global imap
	
	imap.select(folder, True);
	rv, search = imap.search(None, 'ALL');
	print (search);
	folderCount = len(search[0].split());
	
	timestamps = []
	# based on https://gist.github.com/robulouski/7441883	
	for num in search[0].split():
		rv, data = imap.fetch(num, '(RFC822)')
		if rv != 'OK':
			print("ERROR getting message", num)
			return
		
		msg = email.message_from_bytes(data[0][1])
		hdr = email.header.make_header(email.header.decode_header(msg['Subject']))
		subject = str(hdr)
		#print('Message %s: %s' % (num, subject))
		#print('Raw Date:', msg['Date'])
		# Now convert to local date-time
		date_tuple = email.utils.parsedate_tz(msg['Date'])
		if date_tuple:
			timestamp = email.utils.mktime_tz(date_tuple)
			#print ("Timestamp:", timestamp)
			timestamps.append(timestamp)
	

	return (folderCount, timestamps);

def getDataForToday():
	inboxCount, inboxTimestamps = countFolder('INBOX');
	uniCount, uniTimestamps = countFolder('Uni');
	#print (inboxTimestamps, mean(inboxTimestamps), );
	
	return (str(inboxCount), str(uniCount), int(datetime.datetime.utcnow().strftime("%s"))-mean(inboxTimestamps), int(datetime.datetime.utcnow().strftime("%s"))-mean(uniTimestamps));

def storeData():
	data = getDataForToday();
	with open("/home/florin/bin/QuantifiedSelf/Mails/inbox.data", "a") as myfile:
		myfile.write(datetime.datetime.utcnow().strftime("%s")+"	"+data[0]+"	"+data[1]+"	"+str(data[2])+"	"+str(data[3])+"\n");
		
def getData():
	with open("/home/florin/bin/QuantifiedSelf/Mails/inbox.data") as f:
		content = f.readlines()

	data = []
	for item in content:
		items = item.rstrip().split("\t")
		#print(items)
		data.append(items)
	
	return data;

if __name__ == '__main__':
	login();
	storeData();
	getDataForToday();
	#plot(getData());
