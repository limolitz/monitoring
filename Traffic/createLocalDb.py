#!/usr/bin/env python
import sqlite3 as sql
import argparse

parser = argparse.ArgumentParser(description='Initializes the local database for traffic logging.')
parser.add_argument('--dropDB', action='store_true', help='Drop database if it already exists')
args = parser.parse_args()

dbConnection = sql.connect('traffic.db')
with dbConnection:
        dbCursor = dbConnection.cursor()
        if args.dropDB:
                dbCursor.execute("DROP TABLE IF EXISTS traffic")
        dbCursor.execute("CREATE TABLE traffic (date INT PRIMARY KEY, trafficRX INT, trafficTX INT, uptime INT, totalTrafficRX INT, totalTrafficTX int)")