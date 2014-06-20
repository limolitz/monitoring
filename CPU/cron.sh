#!/bin/bash
cd /home/florin/bin/QuantifiedSelf/CPU
TZ=UTC python loadAverages.py
TZ=UTC gnuplot loadAverages.plot
scp cpu.png leo:/home/florin/html/home2/images/cpu_kiwi.png