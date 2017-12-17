#!/bin/bash
cd $(dirname "${BASH_SOURCE[0]}")

if [ "$(uname -s)" = "Darwin" ]; then
	export PATH=/usr/local/opt/python3/bin/:$PATH
fi
TZ=UTC python3 loadAverages.py
