set term png truecolor size 1000,500 font "Helvetica, 13pt" 
set title "Inbox Count as of ". system("date +'%H:%M:%S'")
set grid
set grid mxtics
set output "mailsInbox.png"

set xdata time
# parse timestamp
set timefmt "%s"

# set ad day-month
set format x "%d.%m."

# tic with 1 day
set xtic 86400
set xlabel "Date"
set autoscale x

set ytic 5
set ylabel "# of Mails"
set yrange [0:]

set y2range [0:]
set y2label "Average Age of Mails in days"
set y2tic 60

set key center bottom outside horizontal

set style fill solid 1.0
set style data boxes	

plot "inbox.data" using 1:2 title "# Inbox" with lines lc rgb 'blue', "inbox.data" using 1:3 title "# Uni" with lines lc rgb 'green', "inbox.data" using 1:($4/(60*60)) title "Avg. Age of Inbox Mails" axes x1y2 with lines lt 3, "inbox.data" using 1:($5/(60*60)) title "Avg. Age of Uni Mails" axes x1y2 with lines lt 4
