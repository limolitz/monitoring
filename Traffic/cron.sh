#!/bin/bash
cd /home/florin/bin/QuantifiedSelf/Traffic
python countTraffic.py
python plot.py 21
scp traffic.png leo:/home/florin/html/home2/images/