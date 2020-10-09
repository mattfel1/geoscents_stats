#!/bin/bash
for commit in $(git rev-list $branch)
do
    if git ls-tree --name-only -r $commit | grep -q '\.hbm\.xml$'; then
        echo $commit
        exit 0
    fi
done
