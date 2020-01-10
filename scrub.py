import os
import ipinfo
import json
from pathlib import Path
import urllib.request
import re

pathlist = Path('.').glob('**/*_guesses')
cache = {'127.0.0.1': ["Unknown", "Unknown"]}

for path in pathlist:
    # because path is object not string
    file = str(path)
    print(file)
    
    with open(file) as json_file:
        data = json.load(json_file)
        for entry in data:
            data[entry]['regions'] = []
            data[entry]['countries'] = []
            for ip in data[entry]['ips']:
                ip4 = '.'.join(re.split(':|\.',ip)[-4:])
                if (ip4 in cache):
                    data[entry]['regions'].append(cache[ip4][0])
                    data[entry]['countries'].append(cache[ip4][1])
                else:
                    access_token = 'a0d2f9a2e477c0' # Please get your own free token instead of using mine :(
                    handler = ipinfo.getHandler(access_token)
                    details = handler.getDetails(ip4)
                    cache[ip4] = [details.region, details.country_name]
                    data[entry]['regions'].append(details.region)
                    data[entry]['countries'].append(details.country_name)
            data[entry].pop('ips', None)
            # Hacky way to put the statistics summaries at the beginning of json entry
            data[entry]['dists'] = data[entry].pop('dists',None)
            data[entry]['times'] = data[entry].pop('times',None)
        outfile = file.replace('.','').replace(' ','').replace('_guesses','') + '.json'
        with open(outfile, 'w') as data_file:
            json.dump(data, data_file, indent=2)
        os.remove(file)

        subprocess.call(['./jsontocsv.py', outfile, outfile.replace('.json','.csv')])
