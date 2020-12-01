#!/bin/bash

cd /home/mattfel/geoscents_stats
# git reset --hard
# git pull
./transfer.sh

# Merge new data into base files and wipe out new data
python3 merge.py World | tee /tmp/geoscents_stats_log
python3 merge.py Europe | tee /tmp/geoscents_stats_log
python3 merge.py Africa | tee /tmp/geoscents_stats_log
python3 merge.py Asia | tee /tmp/geoscents_stats_log
python3 merge.py Oceania | tee /tmp/geoscents_stats_log
python3 merge.py Trivia | tee /tmp/geoscents_stats_log
python3 merge.py "N. America" | tee /tmp/geoscents_stats_log
python3 merge.py "S. America" | tee /tmp/geoscents_stats_log

# Scrub
python3 scrub.py | tee /tmp/geoscents_stats_log
bash growth.sh

# git add -A
# git commit -m "auto-update"
# git push
