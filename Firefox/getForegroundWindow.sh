#!/bin/bash
windowID=$(/usr/bin/xprop -display :0 -root _NET_ACTIVE_WINDOW | /bin/grep -oP "0x[0-9a-f]{2,}")
#echo "WindowID: $windowID"
procID=$(/usr/bin/xprop -display :0 -id $windowID | /bin/grep "_NET_WM_PID" | /bin/grep -o "[0-9]*$")
#echo "ProcID: $procID"
#echo -n "Commandline: "
cat /proc/$procID/cmdline
echo ""
#sleep 5
exit 0
