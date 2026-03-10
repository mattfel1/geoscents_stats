import os
import geoip2.database
import json
from pathlib import Path
import numpy as np
import re
import glob
from concurrent.futures import ProcessPoolExecutor, as_completed

debug = False
home = os.environ['HOME']
staging_dir = home + '/geoscents_stats/staging/'
out_dir_folder = 'data/'
out_dir = home + '/geoscents_stats/' + out_dir_folder

# Download from https://dev.maxmind.com/geoip/geolite2-free-geolocation-data
# (free account required; run: geoipupdate, or manually place the .mmdb here)
MMDB_PATH = home + '/geoscents_stats/GeoLite2-Country.mmdb'

unknown_ip = '127.0.0.1'


def prepopulate_cache(maps, cache):
    """Resolve all uncached IPs across all maps serially (MMDB reader is not fork-safe)."""
    reader = geoip2.database.Reader(MMDB_PATH)
    new_lookups = 0
    for this_map in maps:
        fpath = staging_dir + this_map + "_guesses_base"
        try:
            with open(fpath) as f:
                data = json.load(f)
        except Exception:
            continue
        for entry in data:
            for ip in data[entry].get('ips', []):
                if 'optOut' in ip:
                    continue
                ip4 = '.'.join(re.split(r'[:.t]', ip)[-4:])
                if ip4 not in cache:
                    try:
                        resp = reader.country(ip4)
                        country = resp.country.name or 'Unknown'
                    except Exception:
                        country = None
                    cache[ip4] = [None, country]
                    new_lookups += 1
    reader.close()
    print(f'Pre-populated {new_lookups} new IPs (total cache: {len(cache)})')
    return cache


def handle_map_worker(args):
    """Worker: process one map independently. Returns results to be merged by main thread."""
    staging_dir, this_map, out_dir_folder, cache, unknown_ip, mmdb_path, debug = args

    import geoip2.database
    import json
    import re
    import numpy as np

    # Each worker needs its own reader instance (not fork-safe to share)
    reader = geoip2.database.Reader(mmdb_path)

    local_pc = {'Total': 0, 'Unknown': 0}  # player_countries contribution
    local_ccp = {}                           # continent_country_perf[this_map]
    num_clicks = 0
    num_cities = 0
    metadata_entry = None

    try:
        with open(staging_dir + this_map + "_guesses_base") as f:
            data = json.load(f)

        unknown_country = (cache.get(unknown_ip) or [None, 'Unknown'])[1] or 'Unknown'

        for entry in data:
            num_cities += 1
            data[entry]['regions'] = []
            data[entry]['countries'] = []
            el = 0
            print(f"Processing {len(data[entry]['ips'])} entries for {entry}")

            for ip in data[entry]['ips']:
                num_clicks += 1
                ip4 = '.'.join(re.split(r'[:.t]', ip)[-4:])

                if 'optOut' in ip:
                    country = unknown_country
                elif ip4 in cache and cache[ip4][1]:
                    country = cache[ip4][1]
                elif debug:
                    country = unknown_country
                else:
                    # Fallback: look up IPs missed by prepopulate (should be rare)
                    print(f'Looking up {ip4}')
                    try:
                        resp = reader.country(ip4)
                        country = resp.country.name or 'Unknown'
                    except Exception:
                        country = None
                    if country:
                        cache[ip4] = [None, country]
                    else:
                        cache[ip4] = [None, None]
                        country = unknown_country

                data[entry]['regions'].append(None)
                data[entry]['countries'].append(country)

                # Update player country click count
                if 'optOut' in ip:
                    local_pc['Unknown'] = local_pc.get('Unknown', 0) + 1
                elif debug and ip4 not in cache:
                    local_pc['Unknown'] = local_pc.get('Unknown', 0) + 1
                else:
                    c_key = (cache.get(ip4) or [None, None])[1]
                    if c_key in local_pc:
                        local_pc[c_key] += 1
                    else:
                        local_pc[c_key] = 1
                local_pc['Total'] = local_pc.get('Total', 0) + 1

                # Update continent_country_perf
                c = country if country else 'Unknown'
                if c in local_ccp:
                    local_ccp[c].append(data[entry]['dists'][el])
                else:
                    local_ccp[c] = [data[entry]['dists'][el]]
                el += 1

            data[entry].pop('ips', None)
            data[entry]['dists'] = data[entry].pop('dists', None)
            data[entry]['times'] = data[entry].pop('times', None)

        outfile = out_dir_folder + this_map + '.json'
        with open(outfile, 'w') as f:
            json.dump(data, f, indent=2)

        for e in local_ccp:
            numel = len(local_ccp[e])
            local_ccp[e] = [float(np.mean(local_ccp[e])), numel]

        if num_cities == 0:
            num_cities = 1
        metadata_entry = {
            'num_cities': num_cities,
            'num_clicks': num_clicks,
            'num_clicks_per_city': num_clicks / num_cities
        }
        print(f"writing metadata for {this_map} = {num_cities} cities, {num_clicks} clicks")

    except Exception as e:
        import traceback
        print(f"ERROR processing {this_map}: {e}")
        traceback.print_exc()
    finally:
        reader.close()

    return this_map, local_ccp, metadata_entry, local_pc, num_clicks


# MAIN

try:
    with open('/scratch/ip_cache', 'r') as fp:
        cache = json.load(fp)
        print(f'Loaded {len(cache)} ips from cache')
except Exception:
    cache = {unknown_ip: ['Unknown', 'Unknown']}

metadata = {}
total_num_clicks = 0
player_countries = {'Total': 0, 'Unknown': 0}
continent_country_perf = {}

maps = sorted([
    str(path).split("/")[-1].replace('_guesses_base', '')
    for path in glob.glob(staging_dir + "*_guesses_base")
])

# Phase 1: resolve all uncached IPs serially (MMDB reader is not fork-safe)
cache = prepopulate_cache(maps, cache)

with open('/scratch/ip_cache', 'w') as fp:
    json.dump(cache, fp)
print(f'Cache saved ({len(cache)} entries)')

# Phase 2: process each map in parallel
_max = int(os.environ['MAX_WORKERS']) if os.environ.get('MAX_WORKERS') else (os.cpu_count() or 4)
num_workers = min(_max, len(maps), 16)
print(f'Processing {len(maps)} maps with {num_workers} workers...')

args_list = [
    (staging_dir, m, out_dir_folder, cache, unknown_ip, MMDB_PATH, debug)
    for m in maps
]

with ProcessPoolExecutor(max_workers=num_workers) as executor:
    futures = {executor.submit(handle_map_worker, args): args[1] for args in args_list}
    for future in as_completed(futures):
        map_name = futures[future]
        try:
            this_map, local_ccp, metadata_entry, local_pc, num_clicks = future.result()
            continent_country_perf[this_map] = local_ccp
            if metadata_entry:
                metadata[this_map] = metadata_entry
            total_num_clicks += num_clicks
            for k, v in local_pc.items():
                if k in player_countries:
                    player_countries[k] += v
                else:
                    player_countries[k] = v
        except Exception as e:
            print(f'ERROR merging results for {map_name}: {e}')

metadata['Total'] = {'num_clicks': total_num_clicks}

with open(out_dir + 'player_countries.csv', 'w') as data_file:
    header = [c.strip() for c in maps]
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
                tail.append('"<b>%.1f</b>"' % (weighted / den))
            else:
                try:
                    tail.append('"%.1f"' % continent_country_perf[c][k][0])
                except Exception:
                    tail.append('""')
        if k == 'Total':
            data_file.write('["","<b>%s</b>","<b>%s</b>",%s],\n' % (k, str(value), ','.join(tail)))
        else:
            data_file.write('["","%s","%s",%s],\n' % (k, str(value), ','.join(tail)))

with open('metadata.json', 'w') as data_file:
    json.dump(metadata, data_file, indent=2)
