#!/bin/bash
cd /home/florin/bin/QuantifiedSelf/Traffic
TZ=UTC python countTraffic.py
TZ=UTC python plot.py 7
mv traffic.png traffic-$(uname -n).png
scp traffic-$(uname -n).png leo:/home/florin/html/home2/images/