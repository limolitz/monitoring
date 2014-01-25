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
                dbCursor.execute("DROP TABLE IF EXISTS chrome")
        dbCursor.execute("CREATE TABLE firefox (date INT PRIMARY KEY, profile TEXT, tabs INT)")