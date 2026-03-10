#!/bin/bash
# Push merged _guesses_base files back to the server and reset each _guesses inbox.
# Run after merge.py has populated ~/geoscents_stats/staging/.

STAGING="$HOME/geoscents_stats/staging"
SERVER="root@geoscents.net"
REMOTE_DIR="/scratch/guesses"

echo "Pushing merged _guesses_base files to server..."

for f in "$STAGING"/*_guesses_base; do
    [ -f "$f" ] || continue
    name="${f##*/}"            # basename
    name="${name%_guesses_base}"  # strip suffix

    # Escape spaces for scp remote path
    esc="${name// /\\ }"

    echo "  -> $name"

    # Upload merged base
    scp "$f" "${SERVER}:${REMOTE_DIR}/${esc}_guesses_base"

    # Fix ownership and reset the guesses inbox (truncate to empty)
    ssh "$SERVER" "chown root:root '${REMOTE_DIR}/${name}_guesses_base' && truncate -s 0 '${REMOTE_DIR}/${name}_guesses'"
done

echo "Pushback complete."
