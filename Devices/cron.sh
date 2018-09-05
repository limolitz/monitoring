#!/bin/bash
cd $(dirname "${BASH_SOURCE[0]}")

/usr/bin/python3 callDevices.py >> cron.log
