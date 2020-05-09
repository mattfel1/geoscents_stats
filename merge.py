import os
import ipinfo
import json
from pathlib import Path
import numpy as np
import urllib.request
import re
import subprocess

# Use this script to merge new _guesses with old _guesses, for when the file mysteriously disappears but you have a copy of the old one.


print("Copy the old file and new file directly into this directory, then scp the updated one to the server")
oldMap = './World_guesses_old'
newMap = './World_guesses_new'
fullMap = './World_guesses'

with open(oldMap) as json_file:
    oldData = json.load(json_file)
with open(newMap) as json_file:
    newData = json.load(json_file)

i = 0
for entry in newData:
    if (entry in oldData):
        i = i + 1
        oldData[entry]['ips'] = oldData[entry]['ips'] + newData[entry]['ips']
        oldData[entry]['lats'] = oldData[entry]['lats'] + newData[entry]['lats']
        oldData[entry]['lons'] = oldData[entry]['lons'] + newData[entry]['lons']
        oldData[entry]['times'] = oldData[entry]['times'] + newData[entry]['times']
        oldData[entry]['dists'] = oldData[entry]['dists'] + newData[entry]['dists']
    else:
        print("CANNOT FIND " + entry)
        exit()

# dump results
with open(fullMap, 'w') as fp:
    json.dump(oldData, fp, indent=2)

print("Merged " + str(i) + " new entries into " + fullMap + ".  scp this back to the server!")