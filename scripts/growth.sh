#!/bin/bash
# Append today's click diff to daily_clicks.csv.
# Reads fresh metadata.json (written by geolocate.py just before this runs).

DAILY_FILE="$HOME/geoscents_stats/daily_clicks.csv"
META="$HOME/geoscents_stats/metadata.json"

# Sum all num_clicks from metadata.json
current=$(awk -F': ' '/"num_clicks"/{gsub(/[^0-9]/,"",$2); sum+=$2} END{print sum+0}' "$META")

# Read last recorded total (second field of last data row)
last_total=0
if [ -f "$DAILY_FILE" ] && [ "$(wc -l < "$DAILY_FILE")" -gt 1 ]; then
    last_total=$(tail -1 "$DAILY_FILE" | awk -F',' '{print $2}')
fi

new_clicks=$((current - last_total))
date_str=$(date +%Y-%m-%d)

# Write header if file doesn't exist yet
[ ! -f "$DAILY_FILE" ] && echo "date,total,new_clicks" > "$DAILY_FILE"

echo "$date_str,$current,$new_clicks" >> "$DAILY_FILE"
echo "  Clicks since last run: +$new_clicks  (cumulative total: $current)"
