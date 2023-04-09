#!/bin/bash

# Get click data in staging dir
cd ~/geoscents_stats
rm -rf ~/geoscents_stats/plotter_tmp && mkdir plotter_tmp
cd plotter_tmp
cp ~/geoscents_stats/data/*.json . && rm metadata.json
# Get player location data
cp ~/geoscents_stats/data/player_countries.csv .

#mv ~/plots/* ~/old_plots/
find ~/plots/ -name '*.*' -exec mv {} ~/old_plots/ \;
cp -r ~/geoscents/resources/flags ~/plots/

python3 ~/geoscents_stats/scripts/plot_hist.py

wait

# Plot growth
bash ~/geoscents_stats/scripts/plot_growth.sh

bash ~/geoscents_stats/scripts/plot_transfer.sh
