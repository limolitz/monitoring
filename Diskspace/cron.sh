#!/bin/bash
# check if filename is a symlink
if [[ -L "${BASH_SOURCE[0]}" ]]; then
	cd $(dirname $(readlink "${BASH_SOURCE[0]}"))
else
	cd $(dirname "${BASH_SOURCE[0]}")
fi

if [ "$(uname -s)" = "Darwin" ]; then
	export PATH=/usr/local/opt/python3/bin/:$PATH
fi
TZ=UTC python3 diskspace.py
