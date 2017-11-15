#!/bin/bash
cd $(dirname "${BASH_SOURCE[0]}")
TZ=UTC python loadAverages.py
