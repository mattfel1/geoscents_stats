#!/bin/bash
# Upsert today's click total into daily_clicks.csv (one row per day, replaced if run twice).
# Reads fresh metadata.json (written by geolocate.py just before this runs).

DAILY_FILE="$HOME/geoscents_stats/daily_clicks.csv"
META="$HOME/geoscents_stats/metadata.json"

# Use the pre-summed Total entry written by geolocate.py (avoids double-counting)
current=$(python3 -c "import json; d=json.load(open('$META')); print(d['Total']['num_clicks'])")

# Read the previous day's total (the last row that isn't today)
date_str=$(date +%Y-%m-%d)
last_total=0
if [ -f "$DAILY_FILE" ]; then
    prev=$(grep -v "^date," "$DAILY_FILE" | grep -v "^${date_str}," | tail -1)
    [ -n "$prev" ] && last_total=$(echo "$prev" | cut -d',' -f2)
fi

new_clicks=$((current - last_total))

# Write header if file doesn't exist yet
[ ! -f "$DAILY_FILE" ] && echo "date,total,new_clicks" > "$DAILY_FILE"

# Upsert: remove any existing row for today, then append fresh one
tmpfile=$(mktemp)
grep -v "^${date_str}," "$DAILY_FILE" > "$tmpfile"
echo "$date_str,$current,$new_clicks" >> "$tmpfile"
mv "$tmpfile" "$DAILY_FILE"

echo "  Clicks since last run: +$new_clicks  (cumulative total: $current)"
