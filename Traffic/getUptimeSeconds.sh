#!/bin/bash
export LANG=ALL
if [ "$(uname -s)" = "Darwin" ]; then
	# coreutils via brew
	export PATH=/usr/bin:$PATH
	# adjusted from https://discussions.apple.com/thread/498916?start=0&tstart=0
	uptime | awk '{ sub(/.* up /,""); sub(/, *[^ ]* users.*/,""); DAYS = $0; HOURS = $0; MIN = $0; sub(/ .*/, "", DAYS); sub(/.*, */,"", HOURS); sub(/:.*/, "", HOURS); sub(/.*:/, "", MIN); SEC = ( DAYS*24*60*60 + HOURS*60*60 + MIN*60 ); print SEC }'
else
	export PATH=/bin:$PATH
	# read uptime from /proc/uptime, grep only for first entry and for full seconds
	cat /proc/uptime | grep -oP "^[0-9]*"
fi