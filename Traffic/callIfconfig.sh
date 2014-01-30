#!/bin/bash
LANGUAGE=en_US;
# Grep from http://meinit.nl/shell-script-measure-network-throughput-linux-machines
# received traffic
ifconfig eth0 | grep 'RX bytes' | cut -d: -f2 | awk '{ print $1 }';
# sent traffic
ifconfig eth0 | grep 'TX bytes' | cut -d: -f3 | awk '{ print $1 }';