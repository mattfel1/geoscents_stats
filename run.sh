#!/bin/bash

cd /home/mattfel/geoscents_stats
git reset --hard
git pull
./transfer.sh

python3 scrub.py

git add -A
git commit -m "auto-update"
git push
