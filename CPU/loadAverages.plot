set term png truecolor size 700,400 font "Helvetica, 13pt" 
set title "CPU-Load as of ". system("date +'%H:%M:%S'")." on ".system("uname -n")
set grid xtics
set grid ytics
set output "cpu.png"

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
set ylabel "Load"
set yrange [0:]

set key left top inside horizontal

set style fill solid 1.0
set style data boxes

plot "cpu.data" using 1:2 title "1 min avg" with lines, "cpu.data" using 1:3 title "5 min avg" with lines, "cpu.data" using 1:4 title "15 min avg" with lines


