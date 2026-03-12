#!/bin/bash

cd ~/geoscents_stats/plotter_tmp
cp ~/geoscents_stats/daily_clicks.csv .
python3 ~/geoscents_stats/scripts/plot_growth.py
rm daily_clicks.csv

