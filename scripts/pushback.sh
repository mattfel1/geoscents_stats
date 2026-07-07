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

    echo "  -> $name"

    # Never push a file that isn't valid JSON — a corrupt/truncated local
    # merge must not be allowed to clobber the only copy on the server.
    if ! python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$f" 2>/dev/null; then
        echo "  ERROR: $f is not valid JSON — refusing to push, skipping truncate"
        continue
    fi

    # Use ssh+cat to transfer — avoids scp's literal-path issue with modern OpenSSH
    # on paths containing spaces (scp 9.x sends path verbatim via sftp, not via remote shell).
    # The truncate only runs if the transfer succeeds.
    if ssh "$SERVER" "cat > '${REMOTE_DIR}/${name}_guesses_base'" < "$f"; then
        ssh "$SERVER" "chown root:root '${REMOTE_DIR}/${name}_guesses_base' && truncate -s 0 '${REMOTE_DIR}/${name}_guesses'"
    else
        echo "  ERROR: failed to upload $name — skipping truncate to preserve inbox"
    fi
done

echo "Pushback complete."
