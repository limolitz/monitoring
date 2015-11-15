import paho.mqtt.client as mqtt
import ConfigParser
import ssl
import json
import datetime
import subprocess

def sendMQTT(topic, data):
	config = ConfigParser.ConfigParser()
	config.read("config.ini")

	client = mqtt.Client()

	# Get configuration
	hostname = config.get("Account", "hostname")
	port = config.get("Account", "port")
	username = config.get("Account", "user")
	password = config.get("Account", "password")

	# Connect
	client.username_pw_set(username, password = password)
	client.tls_set(config.get("Account", "cacrtPath"), tls_version=ssl.PROTOCOL_TLSv1_2)
	client.connect(hostname, port, 60)

	uname = subprocess.Popen('uname -n', stdout=subprocess.PIPE, shell=True).stdout.read()

	# Publish a message
	client.publish(topic+"/"+username+"/"+uname, json.dumps(data))