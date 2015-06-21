import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import subprocess
import pylab
import matplotlib.dates as md
import matplotlib.ticker
import datetime

machineName = subprocess.Popen('uname -n', stdout=subprocess.PIPE, shell=True).stdout.read().strip()

datalist = pylab.loadtxt("traffic.data")

dates=[datetime.datetime.utcfromtimestamp(ts) for ts in datalist[:,0]]
print dates[0]
print dates[-1]

fig, ax = plt.subplots()

transmitted = ax.bar(dates, np.add(datalist[:,1],datalist[:,2])/(1024**3), color='r', edgecolor = "none")
received = ax.bar(dates, datalist[:,1]/(1024**3), color='y', edgecolor = "none")

# add some text for labels, title and axes ticks
ax.set_title('Traffic on '+machineName+ " as per "+datetime.datetime.today().strftime("%d.%m.%Y, %H:%M")+" UTC")

ax.set_xlabel('Date (UTC)')
xfmt = md.DateFormatter('%d.%m.')
ax.xaxis.set_major_formatter(xfmt)

ax.set_ylabel('Traffic in GiB')
loc = matplotlib.ticker.MultipleLocator(base=4.0) # this locator puts ticks at regular intervals
ax.yaxis.set_major_locator(loc)

ax.legend((transmitted[0], received[0]), ('Transmitted', 'Received'))

plt.savefig('trafficNew.png')
