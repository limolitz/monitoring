#!/bin/bash
cd /home/florin/bin/QuantifiedSelf/RAM
TZ=UTC python ramUsage.py
TZ=UTC gnuplot ramUsage.plot
scp ram.png leo:/home/florin/html/home2/images/ram_kiwi.png
