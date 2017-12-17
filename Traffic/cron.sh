#!/bin/bash
cd $(dirname "${BASH_SOURCE[0]}")
TZ=UTC ./countTraffic.py
