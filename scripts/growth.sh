#!/bin/bash

echo "Time,Num Clicks" > growth.csv
lastnum=0
for commit in $(git rev-list master --reverse)
do
    num=`git --no-pager show $commit:metadata.json | awk -F': ' '/"num_clicks"/{gsub(/[^0-9]/,"",$2); sum+=$2} END{print sum+0}'`
    time=`git show $commit -s --format=%ct`
    # There was a glitch that caused counts to go from ~2mil to ~30mil that we want to filter out
    thresh=$((lastnum + 3000000))
    if [[ "$num" -gt "$lastnum" && "$num" -gt "10000" && "$num" -lt "$thresh" ]]; then
      echo "$time,$num" >> growth.csv
      lastnum=$num
    fi
done
