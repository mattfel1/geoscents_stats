import matplotlib.pyplot as plt
import csv
import matplotlib.dates as md
import numpy as np
import datetime as dt
import time
from scipy.interpolate import interp2d, interp1d, interpnd

x = []
y = []
unix = []

with open('growth.csv','r') as csvfile:
    plots = csv.reader(csvfile, delimiter=',')
    next(plots)
    for row in plots:
        unix.append(int(row[0]))
        x.append(dt.datetime.fromtimestamp(int(row[0])))
        y.append(int(row[1]))

# Interpolate to get per-week data
Y_inter = interp1d(unix,y)
seconds_per_batch = 86400 * 2 # (2 days)
num_weeks = int((unix[-1] - unix[0]) / seconds_per_batch)
x_pdf = np.linspace(unix[0], unix[-1], num_weeks)
y_pdf = []
x_pdf_data = []
for i in range(1, len(x_pdf)):
	gain = Y_inter(x_pdf[i]) - Y_inter(x_pdf[i-1])
	y_pdf.append(gain)
	# print(" %d to %d = %d" % (x_pdf[i-1], x_pdf[i], gain))
for i in range(0, len(x_pdf)):
	x_pdf_data.append(dt.datetime.fromtimestamp(int(x_pdf[i] + seconds_per_batch)))


# Plot cdf
plt.plot(x,y, color='blue')
plt.xlabel('Date')
plt.ylabel('Total # Clicks', color='blue')

ax=plt.gca()
ax.tick_params(axis='y', colors='blue')
xfmt = md.DateFormatter('%Y-%m-%d')
ax.xaxis.set_major_formatter(xfmt)
plt.xticks( rotation=25 )

# Plot pdf 
ax2 = ax.twinx()  # instantiate a second axes that shares the same x-axis
plt.bar(x_pdf_data[0:-1], y_pdf, (x_pdf_data[1]-x_pdf_data[0])*0.8, color='red', alpha=0.2)
ax2.set_ylabel('# New Clicks (per %d days)' % (int(seconds_per_batch / 86400)), color='red')
ax2.tick_params(axis='y', colors='red')
ax2.set_ylim([0,max(y_pdf) * 2])

plt.title('Number of recorded data points over time')
plt.savefig('$HOME/plots/growth.png', dpi=300, bbox_inches="tight")


# plt.show()
