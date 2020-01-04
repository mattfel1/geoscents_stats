#!/bin/bash

git reset --hard
git pull
scp geoscents.net:/scratch/*_guesses .

python3 scrub.py

git add -A
git commit -m "auto-update"
git push
