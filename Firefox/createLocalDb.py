#!/usr/bin/env python
import sqlite3 as sql
import argparse

parser = argparse.ArgumentParser(description='Initializes the local database for Firefox processes.')
parser.add_argument('--dropDB', action='store_true', help='Drop database if it already exists')
args = parser.parse_args()

dbConnection = sql.connect('firefoxProcesses.db')
with dbConnection:
        dbCursor = dbConnection.cursor()
        if args.dropDB:
                dbCursor.execute("DROP TABLE IF EXISTS tabNumber, focusedSite")
        dbCursor.execute("CREATE TABLE focusedSite (id INT PRIMARY KEY, profile TEXT, host INT, firstVisit INT, time INT)")
        dbCursor.execute("CREATE TABLE tabNumber (date INT PRIMARY KEY, profile TEXT, tabs INT)")
