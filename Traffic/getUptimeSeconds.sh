#!/bin/bash
# read uptime from /proc/uptime, grep only for first entry and for full seconds
/bin/cat /proc/uptime | grep -oP "^[0-9]*"