#!/bin/bash
export LANGUAGE=en_US;
# Grep from http://meinit.nl/shell-script-measure-network-throughput-linux-machines
# received traffic
/sbin/ifconfig eth0 | /bin/grep 'RX bytes' | /usr/bin/cut -d: -f2 | /usr/bin/awk '{ print $1 }';
# sent traffic
/sbin/ifconfig eth0 | /bin/grep 'TX bytes' | /usr/bin/cut -d: -f3 | /usr/bin/awk '{ print $1 }';
