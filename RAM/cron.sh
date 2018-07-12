#!/bin/bash
cd $(dirname "${BASH_SOURCE[0]}")

if [ "$(uname -s)" = "Darwin" ]; then
        export PATH=/usr/local/opt/python3/bin/:$PATH
fi

LANG=POSIX TZ=UTC python3 ramUsage.py >> cron.log
