#!/bin/bash

echo "Time,Num Clicks" > plot.csv
lastnum=0
for commit in $(git rev-list master --reverse)
do
    num=`git --no-pager show $commit:metadata.json  | grep num_clicks | tail -1 | sed "s/.* //g"`
    time=`git show $commit -s --format=%ct`
    if [[ "$num" -gt "$lastnum" ]]; then
      echo "$time,$num" >> plot.csv
      lastnum=$num
    fi
done
