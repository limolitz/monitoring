#!/bin/bash
cd /home/florin/bin/QuantifiedSelf/RAM
TZ=UTC python ramUsage.py
TZ=UTC gnuplot ramUsage.plot
ssh leo true
mv ram.png ram-$(uname -n).png
scp ram-$(uname -n).png leo:/home/florin/html/home2/images/
