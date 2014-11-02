#!/bin/bash
LANG=ALL /usr/bin/uptime | /bin/grep -oP "[0-9].[0-9]{2}, [0-9].[0-9]{2}, [0-9].[0-9]{2}"
