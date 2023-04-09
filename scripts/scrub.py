import os
import ipinfo
import json
from pathlib import Path
import numpy as np
import urllib.request
import re
import subprocess
import time
import glob
from timeout import timeout
import signal
import time
from itertools import count
from multiprocessing import Process

debug = False
home = os.environ['HOME']
staging_dir = home + '/geoscents_stats/staging/'
out_dir_folder = 'data/'
out_dir = home + '/geoscents_stats/' + out_dir_folder

class MyTimeOutException(Exception):
    pass
 
def alarm_handler(signum, frame):
    print("timeout")
    raise MyTimeOutException

def lookup_1(handler, ip4):
    x = handler.getDetails(ip4)
    return x

def lookup_2(ip4):
    # signal.signal(signal.SIGALRM, signal_handler)
    # signal.alarm(1)   # Ten seconds
    try:
        with urllib.request.urlopen("https://geolocation-db.com/jsonp/" + ip4) as url:
            fetch = url.read().decode()
            fetch = json.loads(fetch.split("(")[1].strip(")"))
            return fetch
        return None
    except (ZeroDivisionError):
        print("Timed out!")
        pass
    return None

def handle_map(file, this_map, metadata, cache, continent_country_perf):
    with open(file + "/" + this_map + "_guesses_base") as json_file:
        # access_token = 'a0d2f9a2e477c0' # Please get your own free token instead of using mine :(
        access_token = '83f3ad25438b41' # Please get your own free token instead of using mine :(
        handler = ipinfo.getHandler(access_token)
        num_clicks = 0
        num_cities = 0
        data = json.load(json_file)
        for entry in data:
            num_cities = num_cities + 1
            data[entry]['regions'] = []
            data[entry]['countries'] = []
            el = 0
            # print("Processing " + str(len(data[entry]['ips'])) + " entries for " + entry)
            for ip in data[entry]['ips']:
                num_clicks = num_clicks + 1
                ip4 = '.'.join(re.split(':|\.|t',ip)[-4:])
                # I don't know why this ip hangs, even with timeout set
                if ('optOut' in ip): # or ip4 == "107.128.228.139" or ip4 == "95.208.250.46" or ip4 == "60.241.72.255"):
                    data[entry]['regions'].append(cache[unknown_ip][0])
                    data[entry]['countries'].append(cache[unknown_ip][1])
                elif (ip4 in cache and (cache[ip4][1] != None and cache[ip4][1] != "")):
                    data[entry]['regions'].append(cache[ip4][0])
                    data[entry]['countries'].append(cache[ip4][1])
                elif (debug):
                    data[entry]['regions'].append(cache[unknown_ip][0])
                    data[entry]['countries'].append(cache[unknown_ip][1])
                else:
                    fetched = False
                    print('Get entry for ' + ip4)

                    # Version 1
                    signal.signal(signal.SIGALRM, alarm_handler)
                    signal.alarm(15)
                    try:
                        fetch = lookup_2(ip4)
                        cache[ip4] = [fetch['city'], fetch['country_name']]
                        data[entry]['regions'].append(fetch['city'])
                        data[entry]['countries'].append(fetch['country_name'])
                        if (fetch['country_name'] != "" and fetch['country_name'] != None): fetched = True
                    except:
                        print('urllib to geolocation failed to fetch ip ' + ip4)
                    signal.alarm(0)
                    if (fetched == False):
                        # Version 2
                        signal.signal(signal.SIGALRM, alarm_handler)
                        signal.alarm(5)
                        try: 
                            details = lookup_1(handler, ip4)
                            cache[ip4] = [details.region, details.country_name]
                            data[entry]['regions'].append(details.region)
                            data[entry]['countries'].append(details.country_name)
                            if (details.country_name != None and details.country_name != ""): fetched = True
                        except Exception as e:
                            print('ipinfo failed to fetch ip ' + ip4)
                        signal.alarm(0)

                    if (fetched == False):
                        cache[ip4] = [None,None]
                        data[entry]['regions'].append(cache[unknown_ip][0])
                        data[entry]['countries'].append(cache[unknown_ip][1])

                # Update player country click count
                if ('optOut' in ip):
                    player_countries['Unknown'] = player_countries['Unknown'] + 1 
                elif (debug and ip4 not in cache):
                    player_countries['Unknown'] = player_countries['Unknown'] + 1                     
                elif (cache[ip4][1] in player_countries): 
                    player_countries[cache[ip4][1]] = player_countries[cache[ip4][1]] + 1
                else: 
                    player_countries[cache[ip4][1]] = 1
                player_countries["Total"] = player_countries["Total"] + 1
                # Update player country performance
                if ('optOut' in ip): 
                    if ('Unknown' in continent_country_perf[this_map]):
                        continent_country_perf[this_map]['Unknown'] = continent_country_perf[this_map]['Unknown'] + [data[entry]['dists'][el]]
                    else:
                        continent_country_perf[this_map]['Unknown'] = [data[entry]['dists'][el]]                        
                elif (debug and ip4 not in cache):
                    continent_country_perf[this_map]['Unknown'] = [data[entry]['dists'][el]]                        
                elif (cache[ip4][1] in continent_country_perf[this_map]): 
                    continent_country_perf[this_map][cache[ip4][1]] = continent_country_perf[this_map][cache[ip4][1]] + [data[entry]['dists'][el]]
                else: 
                    continent_country_perf[this_map][cache[ip4][1]] = [data[entry]['dists'][el]]
                # continent_country_perf[this_map]['Total'] = continent_country_perf[this_map]['Total'] + [data[entry]['dists'][el]]
                el = el + 1

            data[entry].pop('ips', None)
            # Hacky way to put the statistics summaries at the beginning of json entry
            data[entry]['dists'] = data[entry].pop('dists',None)
            data[entry]['times'] = data[entry].pop('times',None)
        outfile = out_dir_folder + this_map + '.json'
        with open(outfile, 'w') as data_file:
            json.dump(data, data_file, indent=2)
        
        for e in continent_country_perf[this_map]:
            numel = len(continent_country_perf[this_map][e])
            continent_country_perf[this_map][e] = [np.mean(continent_country_perf[this_map][e]), numel]

        # longest, longestCity = convert(outfile, outfile.replace('.json','.csv'))
        # hack div by 0 fix
        if (num_cities == 0):
            num_cities = 1
        metadata[this_map] = {'num_cities': num_cities, 'num_clicks': num_clicks, 'num_clicks_per_city': num_clicks/num_cities}
        print("writing metadata for " + this_map + " = " + str(num_cities) + " cities, " + str(num_clicks) + " clicks")
        # git ignore these files instead of removing them
        # os.remove(file)
        return num_clicks


# This function not used anymore
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
        try:
            output.write('\t'.join(row) + '\n')
        except:
            print("ERROR ON ROW " + row)
    output.close()
    return longest, longestCity

# MAIN

unknown_ip = '127.0.0.1'

try:
    with open('/scratch/ip_cache', 'r') as fp:
        cache = json.load(fp)
        print('Loaded %d ips from cache' % len(cache))
except:
    cache = {unknown_ip: ["Unknown", "Unknown"]}
metadata = {}

total_num_clicks = 0
player_countries = {'Total': 0, 'Unknown': 0}
continent_country_perf = {}

classic_maps = ['World', 'Trivia', 'Europe', 'Africa', 'Asia', 'Oceania', 'N. America', 'S. America']
other_maps = []
maps = classic_maps

for path in glob.glob(staging_dir + "*_guesses_base"):
    file = str(path)
    this_map = file.split("/")[-1].replace('_guesses_base','')

    if (this_map in classic_maps):
        print(file)
    elif (this_map not in classic_maps):
        other_maps.append(this_map)
        print(file)

other_maps.sort()
maps += other_maps

for this_map in maps:
    if (this_map in classic_maps):
        continent_country_perf[this_map] = {}
        map_num_clicks = handle_map(staging_dir, this_map, metadata, cache, continent_country_perf)
        total_num_clicks = total_num_clicks + map_num_clicks
    elif (this_map not in classic_maps):
        continent_country_perf[this_map] = {}
        map_num_clicks = handle_map(staging_dir, this_map, metadata, cache, continent_country_perf)
        total_num_clicks = total_num_clicks + map_num_clicks


with open('/scratch/ip_cache', 'w') as fp:
    json.dump(cache, fp)

metadata['Total'] = {'num_clicks': total_num_clicks}

with open(out_dir + 'player_countries.csv', 'w') as data_file:
    header = []
    for c in maps:
        header.append(c.strip())
    data_file.write('[Player Country,Total Clicks,' + ','.join(header) + ']\n')
    for key, value in sorted(player_countries.items(), key=lambda item: item[1], reverse=True):
        k = key if (key != None) else "Unknown" 
        tail = []
        for c in maps:
            if (k == 'Total'):
                weighted = np.sum([continent_country_perf[c][ct][0]*continent_country_perf[c][ct][1] for ct in continent_country_perf[c]])
                den = np.sum([continent_country_perf[c][ct][1] for ct in continent_country_perf[c]])
                if (den == 0):
                    den = 1
                tail = tail + ['"<b>%.1f</b>"' % (weighted / den)]
            else:
                try:
                    tail = tail + ['"%.1f"' % continent_country_perf[c][k][0]]
                except:
                    tail = tail + ['""']
        if (k == 'Total'): data_file.write('["","<b>%s</b>","<b>%s</b>",%s],\n' % (k, str(value), ','.join(tail)))
        else: data_file.write('["","%s","%s",%s],\n' % (k, str(value), ','.join(tail)))
        # data_file.write('{:25s},'.format(k) + str(value) + "\n")

with open('metadata.json', 'w') as data_file:
    json.dump(metadata, data_file, indent=2)

