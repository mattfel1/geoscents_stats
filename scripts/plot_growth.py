import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as md
import csv
import os
import numpy as np
import datetime as dt

dates = []
new_clicks = []

with open('daily_clicks.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        n = int(row['new_clicks'])
        d = dt.datetime.strptime(row['date'], '%Y-%m-%d')
        dates.append(d)
        new_clicks.append(n)

if len(dates) < 2:
    print('Not enough data yet to plot growth.')
    import sys; sys.exit(0)

fig, ax = plt.subplots(figsize=(14, 5))

bar_color = ['#2196F3' if n >= 0 else '#e53935' for n in new_clicks]
ax.bar(dates, new_clicks, color=bar_color, alpha=0.7, label='New clicks per run', width=0.8)

# Rolling 7-day average (only draw once we have enough points)
window = 7
if len(new_clicks) >= window:
    rolling = np.convolve(new_clicks, np.ones(window) / window, mode='valid')
    rolling_dates = dates[window - 1:]
    ax.plot(rolling_dates, rolling, color='red', linewidth=2, label='7-run avg')

ax.set_xlabel('Date')
ax.set_ylabel('New Clicks per Run')
ax.set_title('GeoScents Activity — New Clicks Per Day')
ax.xaxis.set_major_formatter(md.DateFormatter('%b %d'))
ax.xaxis.set_major_locator(md.WeekdayLocator(byweekday=md.MO))
plt.xticks(rotation=30, ha='right')
ax.legend()
ax.set_ylim(bottom=0)
plt.tight_layout()
plt.savefig(os.environ['HOME'] + '/plots/growth.png', dpi=150, bbox_inches='tight')
print('  growth.png written.')
