#!/bin/bash

echo "Time,Num Clicks" > growth.csv
lastnum=0
for commit in $(git rev-list master --reverse)
do
    num=`git --no-pager show $commit:metadata.json  | grep num_clicks | tail -1 | sed "s/.* //g"`
    time=`git show $commit -s --format=%ct`
    if [[ "$num" -gt "$lastnum" && "$num" -gt "10000" ]]; then
      echo "$time,$num" >> growth.csv
      lastnum=$num
    fi
done
