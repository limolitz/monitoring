#!/bin/bash
cd /home/florin/bin/QuantifiedSelf/RAM
TZ=UTC /usr/local/bin/python3.6 ramUsage.py >> cron.log
