#!/bin/bash

LOG_FILE="$HOME/geoscents_stats/run_log"
exec > >(tee -a "$LOG_FILE") 2>&1
echo "===== run.sh started $(date) ====="
# Pass MAX_WORKERS through to Python scripts to cap parallelism.
# Usage: MAX_WORKERS=4 bash run.sh
[ -n "$MAX_WORKERS" ] && echo "  MAX_WORKERS=$MAX_WORKERS"

PERF_LOG=/tmp/geoscents_perf.log
> "$PERF_LOG"
_t()   { date +%s; }
_log() { printf "  %-35s %5ds\n" "$1" "$(( $(_t) - $2 ))" | tee -a "$PERF_LOG"; }

cd $HOME/geoscents_stats

# Activate venv so all python3 calls use the project packages
source "$HOME/geoscents_stats/venv/bin/activate"

T_ALL=$(_t)

T=$(_t)
bash scripts/upload_counts.sh
_log "upload_counts.sh" $T

T=$(_t)
rm -rf tmp staging
mkdir tmp staging
./scripts/download.sh
_log "download.sh (scp from server)" $T

T=$(_t)
python3 scripts/merge.py
echo "Done merging"
_log "merge.py" $T

T=$(_t)
bash scripts/pushback.sh
_log "pushback.sh (scp to server)" $T

T=$(_t)
python3 scripts/geolocate.py
echo "Done geolocating"
_log "geolocate.py" $T

T=$(_t)
bash scripts/growth.sh
echo "Done plotting growth"
_log "growth.sh" $T

T=$(_t)
git add -A && git commit -m "auto-update" && git push
_log "git add+commit+push" $T

T=$(_t)
bash scripts/plot_run.sh
echo "Done plotting"
_log "plot_run.sh (total)" $T

_log "TOTAL" $T_ALL

echo ""
echo "============ TIMING SUMMARY ============"
cat "$PERF_LOG"
echo "========================================"
