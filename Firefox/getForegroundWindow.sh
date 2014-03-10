#!/bin/bash
windowID=$(xprop -root|grep ^_NET_ACTIVE_WINDOW | grep -o "0x[0-9a-f]*")
#echo "WindowID: $windowID"
procID=$(xprop -id $windowID | grep "_NET_WM_PID" | grep -o "[0-9]*$")
#echo "ProcID: $procID"
#echo -n "Commandline: "
cat /proc/$procID/cmdline
echo ""
#sleep 5
exit 0
