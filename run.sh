#!/bin/bash

PERF_LOG=/tmp/geoscents_perf.log
> "$PERF_LOG"
_t()   { date +%s; }
_log() { printf "  %-35s %5ds\n" "$1" "$(( $(_t) - $2 ))" | tee -a "$PERF_LOG"; }

cd $HOME/geoscents_stats
T_ALL=$(_t)

T=$(_t)
git reset --hard && git pull
_log "git reset+pull" $T

T=$(_t)
rm -rf tmp staging && mkdir tmp staging
./scripts/transfer.sh
_log "transfer.sh (scp from server)" $T

T=$(_t)
python3 scripts/merge.py
echo "Done merging"
_log "merge.py" $T

T=$(_t)
python3 scripts/scrub.py
echo "Done scrubbing"
_log "scrub.py" $T

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
