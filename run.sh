#!/bin/bash

cd $HOME/geoscents_stats
git reset --hard
git pull

rm -rf tmp/*
rm -rf staging/*
./scripts/transfer.sh

# Merge new data into base files and wipe out new data
python3 scripts/merge.py

echo "Done merging"

# Scrub personal identifying information and convert to json
python3 scripts/scrub.py

echo "Done scrubbing"

# Generate growth plot
bash scripts/growth.sh

echo "Done plotting growth"

git add -A
git commit -m "auto-update"
git push

bash scripts/plot_run.sh
echo "Done plotting"