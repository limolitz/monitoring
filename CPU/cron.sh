#!/bin/bash
cd /home/florin/bin/QuantifiedSelf/CPU
TZ=UTC python loadAverages.py
TZ=UTC gnuplot loadAverages.plot
mv cpu.png cpu-$(uname -n).png
ssh leo true
scp cpu-$(uname -n).png leo:/home/florin/html/home2/images/

