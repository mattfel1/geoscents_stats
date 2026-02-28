import os
import geoip2.database
import json
from pathlib import Path
import numpy as np
import re
import glob

debug = False
home = os.environ['HOME']
staging_dir = home + '/geoscents_stats/staging/'
out_dir_folder = 'data/'
out_dir = home + '/geoscents_stats/' + out_dir_folder

# Download from https://dev.maxmind.com/geoip/geolite2-free-geolocation-data
# (free account required; run: geoipupdate, or manually place the .mmdb here)
MMDB_PATH = home + '/geoscents_stats/GeoLite2-Country.mmdb'

reader = geoip2.database.Reader(MMDB_PATH)


def lookup_country(ip4):
    try:
        response = reader.country(ip4)
        return response.country.name or 'Unknown'
    except Exception:
        return None


def handle_map(file, this_map, metadata, cache, continent_country_perf):
    with open(file + "/" + this_map + "_guesses_base") as json_file:
        num_clicks = 0
        num_cities = 0
        data = json.load(json_file)
        for entry in data:
            num_cities = num_cities + 1
            data[entry]['regions'] = []
            data[entry]['countries'] = []
            el = 0
            print("Processing " + str(len(data[entry]['ips'])) + " entries for " + entry)
            for ip in data[entry]['ips']:
                num_clicks = num_clicks + 1
                ip4 = '.'.join(re.split(r'[:.t]', ip)[-4:])

                if 'optOut' in ip:
                    country = cache[unknown_ip][1]
                elif ip4 in cache and cache[ip4][1]:
                    country = cache[ip4][1]
                elif debug:
                    country = cache[unknown_ip][1]
                else:
                    print('Looking up ' + ip4)
                    country = lookup_country(ip4)
                    if country:
                        cache[ip4] = [None, country]
                    else:
                        cache[ip4] = [None, None]
                        country = cache[unknown_ip][1]

                data[entry]['regions'].append(None)
                data[entry]['countries'].append(country)

                # Update player country click count
                if 'optOut' in ip:
                    player_countries['Unknown'] = player_countries['Unknown'] + 1
                elif debug and ip4 not in cache:
                    player_countries['Unknown'] = player_countries['Unknown'] + 1
                elif cache[ip4][1] in player_countries:
                    player_countries[cache[ip4][1]] = player_countries[cache[ip4][1]] + 1
                else:
                    player_countries[cache[ip4][1]] = 1
                player_countries['Total'] = player_countries['Total'] + 1

                # Update player country performance
                c = country if country else 'Unknown'
                if c in continent_country_perf[this_map]:
                    continent_country_perf[this_map][c] = continent_country_perf[this_map][c] + [data[entry]['dists'][el]]
                else:
                    continent_country_perf[this_map][c] = [data[entry]['dists'][el]]
                el = el + 1

            data[entry].pop('ips', None)
            data[entry]['dists'] = data[entry].pop('dists', None)
            data[entry]['times'] = data[entry].pop('times', None)

        outfile = out_dir_folder + this_map + '.json'
        with open(outfile, 'w') as data_file:
            json.dump(data, data_file, indent=2)

        for e in continent_country_perf[this_map]:
            numel = len(continent_country_perf[this_map][e])
            continent_country_perf[this_map][e] = [np.mean(continent_country_perf[this_map][e]), numel]

        if num_cities == 0:
            num_cities = 1
        metadata[this_map] = {'num_cities': num_cities, 'num_clicks': num_clicks, 'num_clicks_per_city': num_clicks / num_cities}
        print("writing metadata for " + this_map + " = " + str(num_cities) + " cities, " + str(num_clicks) + " clicks")
        return num_clicks


# MAIN

unknown_ip = '127.0.0.1'

try:
    with open('/scratch/ip_cache', 'r') as fp:
        cache = json.load(fp)
        print('Loaded %d ips from cache' % len(cache))
except Exception:
    cache = {unknown_ip: ['Unknown', 'Unknown']}
metadata = {}

total_num_clicks = 0
player_countries = {'Total': 0, 'Unknown': 0}
continent_country_perf = {}

classic_maps = ['World', 'Trivia', 'Europe', 'Africa', 'Asia', 'Oceania', 'N. America', 'S. America']
other_maps = []
maps = classic_maps

for path in glob.glob(staging_dir + "*_guesses_base"):
    file = str(path)
    this_map = file.split("/")[-1].replace('_guesses_base', '')
    if this_map not in classic_maps:
        other_maps.append(this_map)

other_maps.sort()
maps += other_maps

for this_map in maps:
    continent_country_perf[this_map] = {}
    map_num_clicks = handle_map(staging_dir, this_map, metadata, cache, continent_country_perf)
    total_num_clicks = total_num_clicks + map_num_clicks

reader.close()

with open('/scratch/ip_cache', 'w') as fp:
    json.dump(cache, fp)

metadata['Total'] = {'num_clicks': total_num_clicks}

with open(out_dir + 'player_countries.csv', 'w') as data_file:
    header = []
    for c in maps:
        header.append(c.strip())
    data_file.write('[Player Country,Total Clicks,' + ','.join(header) + ']\n')
    for key, value in sorted(player_countries.items(), key=lambda item: item[1], reverse=True):
        k = key if (key is not None) else 'Unknown'
        tail = []
        for c in maps:
            if k == 'Total':
                weighted = np.sum([continent_country_perf[c][ct][0] * continent_country_perf[c][ct][1] for ct in continent_country_perf[c]])
                den = np.sum([continent_country_perf[c][ct][1] for ct in continent_country_perf[c]])
                if den == 0:
                    den = 1
                tail = tail + ['"<b>%.1f</b>"' % (weighted / den)]
            else:
                try:
                    tail = tail + ['"%.1f"' % continent_country_perf[c][k][0]]
                except Exception:
                    tail = tail + ['""']
        if k == 'Total':
            data_file.write('["","<b>%s</b>","<b>%s</b>",%s],\n' % (k, str(value), ','.join(tail)))
        else:
            data_file.write('["","%s","%s",%s],\n' % (k, str(value), ','.join(tail)))

with open('metadata.json', 'w') as data_file:
    json.dump(metadata, data_file, indent=2)
