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

tmp_dir = os.environ['HOME'] + '/geoscents_stats/tmp/'
staging_dir = os.environ['HOME'] + '/geoscents_stats/staging/'
processed_data = []

# List of target names that I changed recently, from old name to new name.  
name_changes = {
    ""
}

# Use this script to merge two _guesses files
for file in glob.glob(tmp_dir + "*_guesses*"):
    # Scrub _guesses
    x = file.split('/')[-1].replace("_guesses_base","")
    x = x.replace("_guesses","")
    clean_name = x.replace(".", "")
    clean_name = clean_name.replace(" ", "")
    clean_name = clean_name.lower()
    if (x in processed_data):
        continue

    processed_data.append(x)

    stub_name = x + '_guesses'
    base_file = tmp_dir + x + "_guesses_base"
    staged_file = staging_dir + x + "_guesses_base"
    other_file = tmp_dir + x + "_guesses"
 
    # Populate with empty json if files are empty (TODO how to just check if file exists?)
    base_size = 0
    other_size = 0
    try:
        base_size = os.stat(base_file).st_size
    except:
        base_size = 0
    try:
        other_size = os.stat(other_file).st_size
    except:
        other_size = 0

    
    if base_size == 0:
        f = open(base_file, "w")
        f.write("{}")
        f.close()
    if other_size == 0:
        f = open(other_file, "w")
        f.write("{}")
        f.close()


    with open(base_file) as json_file:
        base_data = json.load(json_file)

    with open(other_file) as json_file:
        new_data = json.load(json_file)

    for entry in new_data:
        if (entry in base_data):
            base_data[entry]['ips'] = base_data[entry]['ips'] + new_data[entry]['ips']
            base_data[entry]['lats'] = base_data[entry]['lats'] + new_data[entry]['lats']
            base_data[entry]['lons'] = base_data[entry]['lons'] + new_data[entry]['lons']
            base_data[entry]['times'] = base_data[entry]['times'] + new_data[entry]['times']
            base_data[entry]['dists'] = base_data[entry]['dists'] + new_data[entry]['dists']
        else:
            base_data[entry] = new_data[entry]

    # Manually merge target name changes
    for key in name_changes:
        if (key in base_data):
            print("Merging " + key + " (" + str(len(base_data[key])) + " entries) into " + name_changes[key] + " (" + str(len(base_data[name_changes[key]])) + " entries)")
            new = base_data[name_changes[key]]
            base_data[key]['ips'] = base_data[key]['ips'] + base_data[name_changes[key]]['ips']
            base_data[key]['lats'] = base_data[key]['lats'] + base_data[name_changes[key]]['lats']
            base_data[key]['lons'] = base_data[key]['lons'] + base_data[name_changes[key]]['lons']
            base_data[key]['times'] = base_data[key]['times'] + base_data[name_changes[key]]['times']
            base_data[key]['dists'] = base_data[key]['dists'] + base_data[name_changes[key]]['dists']
            del base_data[key]

    total = 0
    for entry in base_data:
        total = total + len(base_data[entry]['ips'])
    print("total points for " + x + " = " + str(total))

    # print("Merged " + str(len(new_data)) + " entries into base for " + clean_name)
        
    # dump results
    with open(staged_file, 'w') as fp:
        json.dump(base_data, fp, indent=2)

print("You may now safely scp the _guesses_base back to the server and rm the regular *_guesses file on the server!")
for x in processed_data:
    name = x.replace(" ", "\\ ")
    print("  ssh root@geoscents.net 'sudo su -c \"rm /scratch/guesses/" + name + "_guesses_base\"'")
    print("  scp " + staging_dir + name + "_guesses_base root@geoscents.net:/scratch/guesses/" + name + "_guesses_base")
    print("  ssh root@geoscents.net 'sudo su -c \"chown root:root /scratch/guesses/" + name + "_guesses_base\"'")
    print("  ssh root@geoscents.net 'sudo su -c \"rm /scratch/guesses/" + name + "_guesses\"'")
    print("  ssh root@geoscents.net 'sudo su -c \"touch /scratch/guesses/" + name + "_guesses\"'")
