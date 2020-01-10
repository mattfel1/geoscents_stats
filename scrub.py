import os
import ipinfo
import json
from pathlib import Path
import urllib.request
import re
import subprocess


def convert(fileInput, fileOutput):
    import csv, json, sys
    import numpy as np
    inputFile = open(fileInput) #open json file
    outputFile = open(fileOutput, 'w') #load csv file
    data = json.load(inputFile) #load json content
    inputFile.close() #close the input file
    output = csv.writer(outputFile) #create a csv.write
    longest = 0
    for row in data.keys():
        if (len(data[row]['dists']) > longest): longest = len(data[row]['dists'])
    print(longest)
    header = ['citystring', 'mean_dist', 'std_dist', 'mean_time', 'std_time', 'num_guesses'] + ['dists%d' % i for i in range(longest)] + ['times%d' % i for i in range(longest)] + ['region%d' % i for i in range(longest)] + ['country%d' % i for i in range(longest)]
    outputFile.write('\t'.join(header) + '\n')
    for row in data.keys():
        #print(data[row])
        l = data[row]
        try:
            dists = ['' if (i >= len(l['dists'])) else str(x) for i,x in enumerate(l['dists'])]
            times = ['' if (i >= len(l['times'])) else str(x) for i,x in enumerate(l['times'])]
            regions = ['' if (i >= len(l['regions'])) else str(x) for i,x in enumerate(l['regions'])]
            countries = ['' if (i >= len(l['countries'])) else str(x) for i,x in enumerate(l['countries'])]
            st = '%s\t%s\t%s\t%s\t%s\t%d\t' % (row, l['mean_dist'], l['std_dist'], l['mean_time'], l['std_time'], len(l['dists'])) + ('\t'.join(dists)) + ('\t'.join(times)) + ('\t'.join(regions)) + ('\t'.join(countries))
            outputFile.write(st + '\n') #values row
        except:
            print('Error on %s' % row)

    outputFile.close()


    lines = csv.reader(open(fileOutput), delimiter="\t")
    reader = []
    for r in lines:
        reader.append(r)
    header = reader.pop(0)
    def toFlt(x):
        try:
            return float(x)
        except:
            return -1.0
    sortedlist = sorted(reader, key=lambda row: toFlt(row[1]), reverse=True)
    output = open(fileOutput, 'w')
    output.write('\t'.join(header) + '\n')
    for row in sortedlist:
        output.write('\t'.join(row) + '\n')
    output.close()


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

        convert(outfile, outfile.replace('.json','.csv'))
