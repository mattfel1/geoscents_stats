#!/bin/bash

cd ~/geoscents_stats/plotter_tmp
cp ~/geoscents_stats/growth.csv .
python3 ~/geoscents_stats/scripts/plot_growth.py
rm growth.csv

