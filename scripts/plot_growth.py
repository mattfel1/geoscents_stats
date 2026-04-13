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
totals = []

with open('daily_clicks.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        n = int(row['new_clicks'])
        t = int(row['total'])
        d = dt.datetime.strptime(row['date'], '%Y-%m-%d')
        dates.append(d)
        new_clicks.append(n)
        totals.append(t)

if len(dates) < 2:
    print('Not enough data yet to plot growth.')
    import sys; sys.exit(0)

fig, ax1 = plt.subplots(figsize=(14, 5))

# Bar chart: new clicks per run
bar_color = ['#2196F3' if n >= 0 else '#e53935' for n in new_clicks]
ax1.bar(dates, new_clicks, color=bar_color, alpha=0.7, label='New clicks per day', width=0.8)

# Rolling 7-run average
window = 7
if len(new_clicks) >= window:
    rolling = np.convolve(new_clicks, np.ones(window) / window, mode='valid')
    rolling_dates = dates[window - 1:]
    ax1.plot(rolling_dates, rolling, color='red', linewidth=2, label='7-run avg')

ax1.set_xlabel('Date')
ax1.set_ylabel('New Clicks per Day', color='#333')
ax1.set_ylim(bottom=0)
ax1.xaxis.set_major_formatter(md.DateFormatter('%b %d'))
ax1.xaxis.set_major_locator(md.WeekdayLocator(byweekday=md.MO))
plt.xticks(rotation=30, ha='right')

# Secondary axis: cumulative total
ax2 = ax1.twinx()
ax2.plot(dates, totals, color='#9c27b0', linewidth=1.5, linestyle='--', label='Cumulative total', alpha=0.8)
ax2.set_ylabel('Cumulative Total Clicks', color='#9c27b0')
ax2.tick_params(axis='y', labelcolor='#9c27b0')
ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x/1e6:.3f}M'))

# Combine legends
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

ax1.set_title('GeoScents Activity — Daily New Clicks + Cumulative Total')
plt.tight_layout()
plt.savefig(os.environ['HOME'] + '/plots/growth.png', dpi=150, bbox_inches='tight')
print('  growth.png written.')
