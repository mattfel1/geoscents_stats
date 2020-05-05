import os
import ipinfo
import json
from pathlib import Path
import numpy as np
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
    longestCity = ''
    for row in data.keys():
        if (len(data[row]['dists']) > longest): 
            longest = len(data[row]['dists'])
            longestCity = row
    header = ['citystring', 'mean_dist', 'std_dist', 'mean_time', 'std_time', 'num_guesses'] + ['dists%d' % i for i in range(longest)] + ['times%d' % i for i in range(longest)] + ['region%d' % i for i in range(longest)] + ['country%d' % i for i in range(longest)] + ['lat%d' % i for i in range(longest)] + ['lon%d' % i for i in range(longest)]
    outputFile.write('\t'.join(header) + '\n')
    for row in data.keys():
        #print(data[row])
        l = data[row]
        try:
            dists = ['' if (i >= len(l['dists'])) else str(l['dists'][i]) for i in range(longest)]
            lats = ['' if (i >= len(l['lats'])) else str(l['lats'][i]) for i in range(longest)]
            lons = ['' if (i >= len(l['lons'])) else str(l['lons'][i]) for i in range(longest)]
            times = ['' if (i >= len(l['times'])) else str(l['times'][i]) for i in range(longest)]
            regions = ['' if (i >= len(l['regions'])) else str(l['regions'][i]) for i in range(longest)]
            countries = ['' if (i >= len(l['countries'])) else str(l['countries'][i]) for i in range(longest)]
            st = '%s\t%s\t%s\t%s\t%s\t%d\t' % (row, l['mean_dist'], l['std_dist'], l['mean_time'], l['std_time'], len(l['dists'])) + ('\t'.join(dists)) + '\t' + ('\t'.join(times)) + '\t' + ('\t'.join(regions)) + '\t' + ('\t'.join(countries)) + '\t' + ('\t'.join(lats)) + '\t' + ('\t'.join(lons))
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
    return longest, longestCity


pathlist = Path('.').glob('**/*_guesses')
try:
    with open('/scratch/ip_cache', 'r') as fp:
        cache = json.load(fp)
        print('Loaded %d ips from cache' % len(cache))
except:
    cache = {'127.0.0.1': ["Unknown", "Unknown"]}
metadata = {}

total_num_clicks = 0
player_countries = {'Total': 0}
continent_order = ['World', 'Trivia', 'Europe', 'Africa', 'Asia', 'Oceania', 'NAmerica', 'SAmerica']
continent_country_perf = {}
for c in continent_order:
    continent_country_perf[c] = {}

for path in pathlist:
    # because path is object not string
    file = str(path)
    continent = file.replace('.','').replace(' ','').replace('_guesses','')
    print(file)
    
    with open(file) as json_file:
        num_clicks = 0
        num_cities = 0
        data = json.load(json_file)
        for entry in data:
            num_cities = num_cities + 1
            data[entry]['regions'] = []
            data[entry]['countries'] = []
            el = 0
            for ip in data[entry]['ips']:
                num_clicks = num_clicks + 1
                ip4 = '.'.join(re.split(':|\.',ip)[-4:])
                if ('optOut' in ip):
                    data[entry]['regions'].append(cache['127.0.0.1'][0])
                    data[entry]['countries'].append(cache['127.0.0.1'][1])
                elif (ip4 in cache):
                    data[entry]['regions'].append(cache[ip4][0])
                    data[entry]['countries'].append(cache[ip4][1])
                else:
                    print(ip4)
                    access_token = 'a0d2f9a2e477c0' # Please get your own free token instead of using mine :(
                    handler = ipinfo.getHandler(access_token)
                    try: 
                        details = handler.getDetails(ip4)
                        cache[ip4] = [details.region, details.country_name]
                        data[entry]['regions'].append(details.region)
                        data[entry]['countries'].append(details.country_name)
                    except:
                        print('failed to fetch ip')
                        data[entry]['regions'].append(cache['127.0.0.1'][0])
                        data[entry]['countries'].append(cache['127.0.0.1'][1])
                # Update player country click count
                if (cache[ip4][1] in player_countries): 
                    player_countries[cache[ip4][1]] = player_countries[cache[ip4][1]] + 1
                else: 
                    player_countries[cache[ip4][1]] = 1
                player_countries["Total"] = player_countries["Total"] + 1
                # Update player country performance
                if (cache[ip4][1] in continent_country_perf[continent]): 
                    continent_country_perf[continent][cache[ip4][1]] = continent_country_perf[continent][cache[ip4][1]] + [data[entry]['dists'][el]]
                else: 
                    continent_country_perf[continent][cache[ip4][1]] = [data[entry]['dists'][el]]
                # continent_country_perf[continent]['Total'] = continent_country_perf[continent]['Total'] + [data[entry]['dists'][el]]
                el = el + 1

            data[entry].pop('ips', None)
            # Hacky way to put the statistics summaries at the beginning of json entry
            data[entry]['dists'] = data[entry].pop('dists',None)
            data[entry]['times'] = data[entry].pop('times',None)
        outfile = file.replace('.','').replace(' ','').replace('_guesses','') + '.json'
        mapname = outfile.replace('.json','')
        with open(outfile, 'w') as data_file:
            json.dump(data, data_file, indent=2)
        
        for e in continent_country_perf[continent]:
            numel = len(continent_country_perf[continent][e])
            continent_country_perf[continent][e] = [np.mean(continent_country_perf[continent][e]), numel]

        longest, longestCity = convert(outfile, outfile.replace('.json','.csv'))
        total_num_clicks = total_num_clicks + num_clicks
        print(num_clicks)
        metadata[mapname] = {'num_cities': num_cities, 'num_clicks': num_clicks, 'num_clicks_per_city': num_clicks/num_cities, 'most_played_city': longestCity, 'most_played_city_num_clicks': longest}
        os.remove(file)


with open('/scratch/ip_cache', 'w') as fp:
    json.dump(cache, fp)

metadata['Total'] = {'num_clicks': total_num_clicks}

with open('player_countries.csv', 'w') as data_file:
    for key, value in sorted(player_countries.items(), key=lambda item: item[1], reverse=True):
        k = key if (key != None) else "unknown" 
        tail = []
        for c in continent_order:
            if (k == 'Total'):
                weighted = np.sum([continent_country_perf[c][ct][0]*continent_country_perf[c][ct][1] for ct in continent_country_perf[c]])
                den = np.sum([continent_country_perf[c][ct][1] for ct in continent_country_perf[c]])
                print(weighted)
                print(den)
                tail = tail + ['"<b>%.1f</b>"' % weighted/den]
            else:
                try:
                    tail = tail + ['"%.1f"' % continent_country_perf[c][k][0]]
                except:
                    tail = tail + ['"-"']
        data_file.write('["%s","%s",%s],\n' % (k, str(value), ','.join(tail)))
        # data_file.write('{:25s},'.format(k) + str(value) + "\n")

with open('metadata.json', 'w') as data_file:
    json.dump(metadata, data_file, indent=2)

