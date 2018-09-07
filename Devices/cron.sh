#!/bin/bash
cd $(dirname "${BASH_SOURCE[0]}")

source bin/activate

python3.7 callDevices.py >> cron.log
