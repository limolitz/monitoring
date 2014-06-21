#!/bin/bash
cd /home/florin/bin/QuantifiedSelf/Traffic
TZ=UTC python countTraffic.py
TZ=UTC python plot.py 1
scp traffic.png leo:/home/florin/html/home2/images/