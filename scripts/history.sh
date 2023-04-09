#!/bin/bash

git log -L59,+1:'metadata.json' > history
cat history | grep "+" | grep "num_clicks" | sed "s/.*: //g"
