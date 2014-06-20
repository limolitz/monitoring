#!/bin/bash
cd /home/florin/bin/QuantifiedSelf/CPU
python loadAverages.py
gnuplot loadAverages.plot
scp cpu.png leo:/home/florin/html/home2/images/cpu_kiwi.png