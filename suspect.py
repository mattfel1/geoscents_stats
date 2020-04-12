import os
import ipinfo
import json
from pathlib import Path
import urllib.request
import re
import subprocess

map = "World"
suspect = '68.129.96.29'

 
pathlist = Path('.').glob('**/' + map + '_guesses')
try:
    with open('/scratch/ip_cache', 'r') as fp:
        cache = json.load(fp)
        print('Loaded %d ips from cache' % len(cache))
except:
    cache = {'127.0.0.1': ["Unknown", "Unknown"]}


for path in pathlist:
    # because path is object not string
    file = str(path)
    
    with open(file) as json_file:
        data = json.load(json_file)
        for entry in data:
            num_cities = num_cities + 1
            data[entry]['regions'] = []
            data[entry]['countries'] = []
            if (suspect in data[entry]['ips']):
                print(entry)
            for i in len(data[entry]['ips']):
                ip = data[entry]['ips'][i]
                if (ip == suspect):
                    print("%6d,%6d" % (data[entry]['dists'][i], data[entry]['times'][i]))
