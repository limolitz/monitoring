set term png truecolor size 700,450 font "Helvetica, 13pt" 
set title "RAM usage as of ". system("date +'%H:%M:%S'") 
set grid xtics
set grid ytics
set output "ram.png"

set style data boxes

# set ad day-month
set xdata time
# parse timestamp
set timefmt "%s"
set format x "%H:%M:%S"
# tic with 1 day
#set xtic '+str(60*60*24*1))
set xtic 60*15
#set xtic 1
set xlabel "Date (UTC)"
set autoscale x

# range automatically set as only data for the last 60 minutes is available
#set xrange [0:0]

#set ytic 1000
set ylabel "Usage in GiB"
set yrange [0:]

set key center bottom outside horizontal

set style fill solid 1.0
set style data boxes

plot "ram.data" using 1:(($3+$4)/1024**2) title "free", "ram.data" using 1:(($4)/1024**2) title "used", "ram.data" using 1:(($5+$6)/1024**2) title "Chrome", "ram.data" using 1:(($5)/1024**2) title "Firefox"


