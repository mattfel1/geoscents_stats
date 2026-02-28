#!/bin/bash

PERF_LOG=/tmp/geoscents_perf.log
_t()   { date +%s; }
_log() { printf "    %-33s %5ds\n" "$1" "$(( $(_t) - $2 ))" | tee -a "$PERF_LOG"; }

echo "  --- plot_run.sh breakdown ---" | tee -a "$PERF_LOG"

T=$(_t)
cd ~/geoscents_stats
rm -rf ~/geoscents_stats/plotter_tmp && mkdir plotter_tmp
cd plotter_tmp
cp ~/geoscents_stats/data/*.json . && rm metadata.json
cp ~/geoscents_stats/data/player_countries.csv .
_log "setup (cp/mkdir)" $T

T=$(_t)
find ~/plots/ -maxdepth 1 -type f -exec mv -t ~/old_plots/ {} +
cp -r ~/geoscents/resources/flags ~/plots/
_log "mv old plots + cp flags" $T

T=$(_t)
python3 ~/geoscents_stats/scripts/plot_hist.py
_log "plot_hist.py" $T

wait

T=$(_t)
bash ~/geoscents_stats/scripts/plot_growth.sh
_log "plot_growth.sh" $T

T=$(_t)
bash ~/geoscents_stats/scripts/plot_transfer.sh
_log "plot_transfer.sh (rsync)" $T
