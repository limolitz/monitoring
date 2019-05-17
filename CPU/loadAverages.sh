#!/bin/bash
export LANG=ALL
if [ "$(uname -s)" = "Darwin" ]; then
	# coreutils and grep via brew
	export PATH=/usr/local/opt/grep/bin:/usr/local/opt/coreutils/bin:$PATH
	guptime | ggrep -oP "[0-9]\.[0-9]{2}, [0-9]\.[0-9]{2}, [0-9]\.[0-9]{2}"
else
	export PATH=/bin:/usr/bin:$PATH
	uptime | grep -oP "[0-9]{1,3}\.[0-9]{2}, [0-9]{1,3}\.[0-9]{2}, [0-9]{1,3}\.[0-9]{2}"
fi
