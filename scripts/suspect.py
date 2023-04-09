import os
import ipinfo
import json
from pathlib import Path
import urllib.request
import re
import subprocess

map = "N. America"
suspect = '68.129.96.29'

tmp_dir = os.environ['HOME'] + '/geoscents_stats/tmp/'

 try:
    with open('/scratch/ip_cache', 'r') as fp:
        cache = json.load(fp)
        print('Loaded %d ips from cache' % len(cache))
except:
    cache = {'127.0.0.1': ["Unknown", "Unknown"]}


for path in glob.glob(tmp_dir + "*_guesses*"):
    # because path is object not string
    file = str(path)
    
    with open(file) as json_file:
        data = json.load(json_file)
        for entry in data:
            ips = [x.replace("::ffff:","") for x in data[entry]['ips']]
            if (suspect in ips):
                print(entry)
            for i in range(len(ips)):
                ip = ips[i]
                if (ip == suspect):
                    print("%6.1f,%1.1f" % (data[entry]['dists'][i], data[entry]['times'][i]))
