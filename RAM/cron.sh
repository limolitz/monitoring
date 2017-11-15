#!/bin/bash
cd $(dirname "${BASH_SOURCE[0]}")
TZ=UTC /usr/local/bin/python3.6 ramUsage.py >> cron.log
