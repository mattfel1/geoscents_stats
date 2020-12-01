import os
import ipinfo
import sys
import json
from pathlib import Path
import numpy as np
import urllib.request
import re
import subprocess
import glob

# Use this script to merge two _guesses files, for when the file mysteriously disappears but you have a copy of the old one, OR for placing the active _guesses into _guesses_full

if (len(sys.argv) != 2):
    print("Please specify the map to apply merging to")

stub_name = sys.argv[1] + '_guesses'
base_name = ''
others = []

for file in glob.glob(stub_name + '*'):
    if (stub_name + "_base" == file):
        base_name = file
    else:
        others.append(file)

if (base_name == ''):
    print("Did not find a base file!")
    exit()
if (len(others) == 0):
    print("Did not find any other files to dump in to the base!")
    exit()

with open(base_name) as json_file:
    base_data = json.load(json_file)

for newMap in others:
    with open(newMap) as json_file:
        new_data = json.load(json_file)

    i = 0
    for entry in new_data:
        if (entry in base_data):
            i = i + 1
            base_data[entry]['ips'] = base_data[entry]['ips'] + new_data[entry]['ips']
            base_data[entry]['lats'] = base_data[entry]['lats'] + new_data[entry]['lats']
            base_data[entry]['lons'] = base_data[entry]['lons'] + new_data[entry]['lons']
            base_data[entry]['times'] = base_data[entry]['times'] + new_data[entry]['times']
            base_data[entry]['dists'] = base_data[entry]['dists'] + new_data[entry]['dists']
        else:
            print("CANNOT FIND " + entry + "... Adding it to base file")
            # exit()
            base_data[entry] = new_data[entry]

    print("Merged " + str(i) + " new entries from " + newMap + " into " + base_name)
    os.remove(newMap)
    
# dump results
with open(base_name, 'w') as fp:
    json.dump(base_data, fp, indent=2)
print("You may now scp the _guesses_base back to the server and rm the regular *_guesses file on the server!")
