import matplotlib.image as mpimg
import scipy.stats as stats 
import csv
import sys
import os
import requests
import json
from pathlib import Path
import random
import urllib.request
from urllib.request import urlopen
import re
import subprocess
import imageio
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import pandas as pd
import glob
from PIL import Image
from timeit import default_timer as timer
import glob

from time import gmtime, strftime
import time


import warnings
warnings.filterwarnings("ignore")


update_stamp = time.strftime("%a, %b %d %Y @ %I:%M %p %Z", time.localtime())
MAP_WIDTH = 1530
MAP_HEIGHT = 900
outdir_prefix = os.environ['HOME'] + '/'
generate_gifs = True
verbose = True

# Copy from geoscents resources/constants.js
url = "https://raw.githubusercontent.com/mattfel1/geoscents/master/resources/maps.json"
response = urlopen(url)
MAP_BOUNDS = json.loads(response.read())

def cleanNameUnderscore(name):
    return name.replace(" ","_").replace(".","_").replace('/','_')

def cleanName(name):
    return name.lower().replace(" ","").replace(".","").replace('/','')

def geoToMerc(room,lat,lon):
    if (room not in MAP_BOUNDS):
        return 0, 0

    min_lon = MAP_BOUNDS[room]["coords"][0];
    max_lon = MAP_BOUNDS[room]["coords"][1];
    max_lat = MAP_BOUNDS[room]["coords"][2];
    zero_lat = MAP_BOUNDS[room]["coords"][3];

    lat_ts = 0

    if (room == "Antarctica" or room == "Arctic"):
        # use Azimuthal Equidistant projection math
        # Lat = radius from origin
        # Lon = angle from origin
        # x = cos(lon) * lat + midpoint
        # y = sin(lon) * lat + midpoint
        # Longitude scaling factor

        # Square map (0 lon is straight up for antarctica, down for arctic)
        sgn = 1;
        outer_lat = max_lat;
        if (room == "Arctic"):
            sgn = -1;
            outer_lat = zero_lat;

        # Scaling factor is number of degrees per pixel
        lat_sf = (zero_lat - max_lat) / (MAP_WIDTH / 2)
        hypot = (lat - outer_lat) / lat_sf

        col = sgn * np.sin(lon * np.pi / 180) * hypot + (MAP_WIDTH / 2)
        row = -np.cos(lon * np.pi / 180) * hypot + (MAP_HEIGHT / 2)
        return col, row

    else:
        # get col value
        if (lon < min_lon):
            col = (lon + 360 - min_lon) * (MAP_WIDTH / (max_lon - min_lon));
        else: 
            col = (lon - min_lon) * (MAP_WIDTH / (max_lon - min_lon));
        # convert from degrees to radians
        latRad = lat * np.pi / 180;

        eqMin = np.arctanh(np.sin(zero_lat * np.pi/180));
        eqRange = np.arctanh(np.sin(max_lat * np.pi/180)) - eqMin;

        # get row value
        row = (MAP_HEIGHT / eqRange) * (np.arctanh(np.sin(latRad)) - eqMin);
        return col, row # transposed in python coords compared to js coords

def initJs(citysrc):
    with open(outdir_prefix + "/plots/" + citysrc + '.js', 'w+') as f:
        f.write("""
$(document).ready(function() {
    $("#all").css("background","yellow");
    const table = $('#%s').DataTable( {
        data: dataSet,
        "lengthChange": true,
        "pageLength": 50,
        "search": {
            "search": ".*",
            "regex": true
        },
        stateSave: true,
        "stateDuration": 60 * 5,
        "dom": '<"top"f>rt<"bottom"ipl><"clear">',
        deferRender:    true,
        "order": [[4, 'asc']],
        columns: [
            { title: "Type", "width": "3%%"},
            { title: "Flag", "width": "3%%"},
            { title: "Country", "width": "5%%" },
            { title: "Admin", "width": "5%%"},
            { title: "City", "width": "10%%" },
            { title: "Avg Dist (km)", "width": "5%%" },
            { title: "Std Dist (km)", "width": "5%%" },
            { title: "# Clicks", "width": "5%%" },
            { title: "Histogram", "width": "5%%"},
            { title: "Game Replay", "width": "5%%"}
        ],
        columnDefs: [
            {
                render: function (data, type, full, meta) {
                    return "<div class='text-wrap width-150'>" + data + "</div>";
                },
                targets: [3,4,5]
            },
            { "type": "alt-string", targets: 1 }
        ],
    } );
    $('#aggregates').on('click', function () {
        $("#aggregates").css("background","yellow");
        $("#entry").css("background","#a9e7f9");
        $("#all").css("background","#a9e7f9");
        table.columns(0).search("Aggregate").draw();
    });
    $('#all').on('click', function () {
        $("#aggregates").css("background","#a9e7f9");
        $("#entry").css("background","#a9e7f9");
        $("#all").css("background","yellow");
        table.columns(0).search("").draw();
    });
    $('#entry').on('click', function () {
        $("#aggregates").css("background","#a9e7f9");
        $("#entry").css("background","yellow");
        $("#all").css("background","#a9e7f9");
        table.columns(0).search("Entry").draw();
    });
    // Hijack ctrl+f to jump to filter bar
    // $(window).keydown(function(e){
    //     if ((e.ctrlKey || e.metaKey) && e.keyCode === 70) {
    //         e.preventDefault();
    //         $('#%s_filter input').focus();
    //         $('#%s_filter input').select();
    //     }
    // });
} );

var dataSet = [
""" % (cleanNameUnderscore(citysrc), citysrc, citysrc))

def writeIndex(header, countries):
    map_names = header[2:]
    map_names_js = '[' + ','.join(['"' + x.replace('\\', '\\\\').replace('"', '\\"') + '"' for x in map_names]) + ']'
    with open(outdir_prefix + "/plots/index.html", 'w+') as f:
        f.write("""<!DOCTYPE html>
<html lang="en">
<head prefix="og: http://ogp.me/ns#">
    <meta charset="UTF-8">
    <meta name="description" content="Plots for Geoscents. An online multiplayer world geography game!  Test your knowledge of city locations." />
    <title>GeoScents Plots</title>
    <link rel="icon" type="image/png" href="https://geoscents.net/resources/favicon.png" sizes="48x48">
    <meta name="GeoScents Plots" content="Plots for Geoscents.  An online multiplayer world geography game!  Test your knowledge of city locations. This is a recreation of the game Geosense from geosense.net.">
    <meta property="og:image" content="https://geoscents.net/resources/ogimage.png" />
    <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
    <script src="https://cdn.datatables.net/1.10.20/js/jquery.dataTables.min.js"></script>
    <link rel="stylesheet" href="https://cdn.datatables.net/1.10.20/css/jquery.dataTables.min.css">
    <link rel="stylesheet" href="theme.css">
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6780905379201491"
         crossorigin="anonymous"></script>
    <style>
table, td, th { border: 1px solid black; }
table { border-collapse: collapse; }
th { height: 50px; }
    </style>
</head>
<body>
<button class="lobby-btn" onclick="window.location.href = 'https://geoscents.net';">Back to Game</button>
<button class="special-room-btn" onclick="window.location.href = 'index.html';">Home</button>
<div class="map-search-wrapper">
    <input type="text" id="map-search" placeholder="Search maps..." autocomplete="off">
    <div id="map-results" class="map-results" style="display:none;"></div>
</div>
<script>
var mapCounts = {};
var mapNames = %s;
function appendMapItem(results, name, matchedCity) {
    var div = document.createElement('div');
    div.className = 'map-result-item';
    var countStr = mapCounts[name] !== undefined ? ' <span class="map-result-count">(' + mapCounts[name].toLocaleString() + ' clicks)</span>' : '';
    var cityStr = matchedCity ? ' <span class="map-result-city">contains &ldquo;' + matchedCity + '&rdquo;</span>' : '';
    div.innerHTML = name + countStr + cityStr;
    div.onclick = function() { window.location.href = name + '.html'; };
    results.appendChild(div);
}
function renderMapList(query) {
    var results = document.getElementById('map-results');
    var q = (query || '').toLowerCase().trim();
    results.innerHTML = '';
    var added = {};
    mapNames.forEach(function(name) {
        if (!q || name.toLowerCase().indexOf(q) !== -1) {
            appendMapItem(results, name, null);
            added[name] = true;
        }
    });
    if (q && window.cityIndex) {
        Object.keys(cityIndex).forEach(function(city) {
            if (city.toLowerCase().indexOf(q) !== -1) {
                cityIndex[city].forEach(function(map) {
                    if (!added[map]) {
                        appendMapItem(results, map, city);
                        added[map] = true;
                    }
                });
            }
        });
    }
    results.style.display = results.children.length ? 'block' : 'none';
}
var searchEl = document.getElementById('map-search');
searchEl.addEventListener('input', function() { renderMapList(this.value); });
searchEl.addEventListener('focus', function() { renderMapList(this.value); });
document.addEventListener('click', function(e) {
    if (!e.target.closest('.map-search-wrapper')) {
        document.getElementById('map-results').style.display = 'none';
    }
});
</script>""" % map_names_js)



        f.write("""<h1>Choose a map from above to view a data table!</h1>
<small>(Last updated %s)</small><br><br>
You can opt-out of contributing to this database by typing /private in the chat box while playing the game. <br><br>
<br><br>
This page is updated approximately every 24 hours.  Raw data can be found <a href="https://github.com/mattfel1/geoscents_stats">here</a>.  <br><br>

<h3>Mean Error by Player Country (<a href="growth.png">Collected Data Points Over Time</a>)</h3>
<table id="index" class="display"></table>
<br><br>

<script type="text/javascript" src="index.js"></script>
<script src="cityIndex.js"></script>
<script src="counts.js"></script>
</body>
</html>
""" % (update_stamp))

    with open(outdir_prefix + "/plots/index.js", 'w+') as f:
        f.write("""
$(document).ready(function() {
    $("#all").css("background","yellow");
    const table = $('#index').DataTable( {
        data: dataSet,
        "lengthChange": true,
        "pageLength": 200,
        "search": {
            "search": ".*",
            "regex": true
        },
        stateSave: true,
        "stateDuration": 60 * 5,
        "dom": '<"top"f>rt<"bottom"ipl><"clear">',
        deferRender:    true,
        "order": [[2, 'des']],
        columns: [
            { title: "", "width": "1%%"},
            """)
        i = 0
        targets = []
        for x in header:
            sfx = "<br>(avg. error, km)" if i > 1 else ""
            f.write("{ title: \"" + x.replace('"','') + sfx + "\", \"width\": \"5%%\"}")
            if (i < len(header) - 1):
                f.write(",\n")
            if (i >= 2):
                targets.append(str(i))

            i = i + 1

        f.write("""],
        columnDefs: [
            {
                render: function (data, type, full, meta) {
                    return "<div class='text-wrap width-150'>" + data + "</div>";
                },
                targets: [""" + ",".join(targets) + """]
            }
        ],
    } );
    table.on( 'order.dt search.dt', function () {
        table.column(0, {search:'applied', order:'applied'}).nodes().each( function (cell, i) {
            cell.innerHTML = i+1;
        } );
    } ).draw();
} );

var dataSet = [ %s ];
""" % countries)

def initCount():
    with open(outdir_prefix + "/plots/counts.js", 'w+') as f:
        f.write("")

def writeCityIndex(city_to_maps):
    with open(outdir_prefix + "/plots/cityIndex.js", 'w+') as f:
        f.write("var cityIndex = " + json.dumps(city_to_maps) + ";")

def writeCount(citysrc, count):
    with open(outdir_prefix + "/plots/counts.js", 'a') as f:
        f.write("\nif (typeof mapCounts !== 'undefined') mapCounts[\"" + citysrc + "\"] = " + str(count) + ";")
        f.write("\nvar _el = document.getElementById(\"" + citysrc + "_count\"); if (_el) _el.innerHTML = \"(" + str(count) + " clicks)\";")

def writeCss():
    with open(outdir_prefix + "/plots/theme.css", 'w+') as f:
        f.write("""
.room-btn {
    cursor: pointer;
    border: 1px solid #333;
    width: 120px;
    padding: 2px 2px;
    margin: 3px 3px;
    font-size: 16px;
    background: #a9e7f9; /* fallback */
    background: -moz-linear-gradient(top,  #a9e7f9 0%, #77d3ef 4%, #05abe0 100%);
    background: -webkit-gradient(linear, left top, left bottom, color-stop(0%,#a9e7f9), color-stop(4%,#77d3ef), color-stop(100%,#05abe0));
    background: -webkit-linear-gradient(top,  #a9e7f9 0%,#77d3ef 4%,#05abe0 100%);
    background: -o-linear-gradient(top,  #a9e7f9 0%,#77d3ef 4%,#05abe0 100%);
    background: -ms-linear-gradient(top,  #a9e7f9 0%,#77d3ef 4%,#05abe0 100%);
    background: linear-gradient(to bottom,  #a9e7f9 0%,#77d3ef 4%,#05abe0 100%);
    border-radius: 2px;
    box-shadow: 0 0 4px rgba(0,0,0,0.3);
}

.lobby-btn {
	cursor: pointer;
	border: 1px solid #333;
	padding: 2px 2px;
	margin: 3px 3px;
	font-size: 16px;
	background: #ffcccc; /* fallback */
	background: -moz-linear-gradient(top,  #ffcccc 0%, #ff9999 4%, #ff6666 100%);
	background: -webkit-gradient(linear, left top, left bottom, color-stop(0%,#ffcccc), color-stop(4%,#ff9999), color-stop(100%,#ff6666));
	background: -webkit-linear-gradient(top,  #ffcccc 0%,#ff9999 4%,#ff6666 100%);
	background: -o-linear-gradient(top,  #ffcccc 0%,#ff9999 4%,#ff6666 100%);
	background: -ms-linear-gradient(top,  #ffcccc 0%,#ff9999 4%,#ff6666 100%);
	background: linear-gradient(to bottom,  #ffcccc 0%,#ff9999 4%,#ff6666 100%);
	border-radius: 2px;
	box-shadow: 0 0 4px rgba(0,0,0,0.3);
}

.special-room-btn {
    cursor: pointer;
    border: 1px solid #333;
    width: 120px;
    padding: 2px 2px;
    margin: 3px 3px;
    font-size: 16px;
    background: #ffe200; /* fallback */
    background: -moz-linear-gradient(top,  #ffe200 0%, #dbc300 4%, #bda800 100%);
    background: -webkit-gradient(linear, left top, left bottom, color-stop(0%,#ffe200), color-stop(4%,#dbc300), color-stop(100%,#bda800));
    background: -webkit-linear-gradient(top,  #ffe200 0%,#dbc300 4%,#bda800 100%);
    background: -o-linear-gradient(top,  #ffe200 0%,#dbc300 4%,#bda800 100%);
    background: -ms-linear-gradient(top,  #ffe200 0%,#dbc300 4%,#bda800 100%);
    background: linear-gradient(to bottom,  #ffe200 0%,#dbc300 4%,#bda800 100%);
    border-radius: 2px;
    box-shadow: 0 0 4px rgba(0,0,0,0.3);
}

.dataTables_filter {
   float: left !important;
}


.filter-btn {
    cursor: pointer;
    border: 1px solid #333;
    width: 200px;
    padding: 2px 2px;
    margin: 3px 3px;
    font-size: 16px;
    background: #a9e7f9; /* fallback */
    border-radius: 2px;
    box-shadow: 0 0 4px rgba(0,0,0,0.3);
}

.map-search-wrapper {
    position: relative;
    display: inline-block;
    width: 300px;
    margin: 10px 3px;
    vertical-align: top;
}

#map-search {
    width: 100%;
    padding: 6px 10px;
    font-size: 16px;
    border: 1px solid #333;
    border-radius: 2px;
    box-sizing: border-box;
}

.map-results {
    position: absolute;
    top: 100%;
    left: 0;
    width: 100%;
    max-height: 400px;
    overflow-y: auto;
    background: white;
    border: 1px solid #999;
    border-top: none;
    z-index: 1000;
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}

.map-result-item {
    padding: 6px 10px;
    cursor: pointer;
    font-size: 15px;
}

.map-result-item:hover {
    background: #a9e7f9;
}

.map-result-count {
    color: #666;
    font-size: 12px;
}

.map-result-city {
    color: #888;
    font-size: 12px;
    font-style: italic;
}
""")
def addJs(entry):
    with open(outdir_prefix + "/plots/" + citysrc + '.js', 'a') as f:
        f.write('[%s],\n' % entry)
    
def finishJs(citysrc):
    with open(outdir_prefix + "/plots/" + citysrc + '.js', 'a') as f:
        f.write("""];""")
    
def trackAdmin(citysrc, country):
    return citysrc == country or country == 'unitedstates' or country == 'canada' or country == 'china' or country == 'india' or country == 'brazil' or country == 'russia' or country == 'australia' or country == 'indonesia'

def stripSpecial(x):
    # return re.sub(r'[^\x00-\x7F]','x', x)
    return re.sub(r'[^A-Za-z0-9\(\),. ]+','_',x)

def writeHtml(citysrc, cols):
    map_names_js = '[' + ','.join(['"' + x.replace('\\', '\\\\').replace('"', '\\"') + '"' for x in cols]) + ']'
    with open(outdir_prefix + "/plots/" + citysrc + '.html', 'w+') as f:
        f.write("""<!DOCTYPE html>
<html lang="en">
<head prefix="og: http://ogp.me/ns#">
    <meta charset="UTF-8">
    <meta name="description" content="Plots for Geoscents. An online multiplayer world geography game!  Test your knowledge of city locations." />
    <title>(%s) GeoScents Plots</title>
    <link rel="icon" type="image/png" href="https://geoscents.net/resources/favicon.png" sizes="48x48">
    <meta name="(%s) GeoScents Plots" content="Plots for Geoscents.  An online multiplayer world geography game!  Test your knowledge of city locations. This is a recreation of the game Geosense from geosense.net.">
    <meta property="og:image" content="https://geoscents.net/resources/ogimage.png" />
    <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
    <script src="https://cdn.datatables.net/1.10.20/js/jquery.dataTables.min.js"></script>
    <link rel="stylesheet" href="https://cdn.datatables.net/1.10.20/css/jquery.dataTables.min.css">
    <link rel="stylesheet" href="theme.css">
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6780905379201491"
         crossorigin="anonymous"></script>
</head>
<body>
<button class="lobby-btn" onclick="window.location.href = 'https://geoscents.net';">Back to Game</button>
<button class="room-btn" onclick="window.location.href = 'index.html';">Home</button>
<div class="map-search-wrapper">
    <input type="text" id="map-search" placeholder="Search maps..." autocomplete="off">
    <div id="map-results" class="map-results" style="display:none;"></div>
</div>
<script>
var mapCounts = {};
var mapNames = %s;
function appendMapItem(results, name, matchedCity) {
    var div = document.createElement('div');
    div.className = 'map-result-item';
    var countStr = mapCounts[name] !== undefined ? ' <span class="map-result-count">(' + mapCounts[name].toLocaleString() + ' clicks)</span>' : '';
    var cityStr = matchedCity ? ' <span class="map-result-city">contains &ldquo;' + matchedCity + '&rdquo;</span>' : '';
    div.innerHTML = name + countStr + cityStr;
    div.onclick = function() { window.location.href = name + '.html'; };
    results.appendChild(div);
}
function renderMapList(query) {
    var results = document.getElementById('map-results');
    var q = (query || '').toLowerCase().trim();
    results.innerHTML = '';
    var added = {};
    mapNames.forEach(function(name) {
        if (!q || name.toLowerCase().indexOf(q) !== -1) {
            appendMapItem(results, name, null);
            added[name] = true;
        }
    });
    if (q && window.cityIndex) {
        Object.keys(cityIndex).forEach(function(city) {
            if (city.toLowerCase().indexOf(q) !== -1) {
                cityIndex[city].forEach(function(map) {
                    if (!added[map]) {
                        appendMapItem(results, map, city);
                        added[map] = true;
                    }
                });
            }
        });
    }
    results.style.display = results.children.length ? 'block' : 'none';
}
var searchEl = document.getElementById('map-search');
searchEl.addEventListener('input', function() { renderMapList(this.value); });
searchEl.addEventListener('focus', function() { renderMapList(this.value); });
document.addEventListener('click', function(e) {
    if (!e.target.closest('.map-search-wrapper')) {
        document.getElementById('map-results').style.display = 'none';
    }
});
</script>""" % (citysrc, citysrc, map_names_js))

        f.write("""<h1>Data Table for %s Map <!-- <a href="all_%s.jpg"><img src="all_%s.jpg" class="img-thumbnail" alt="link" height=75px></a> --> </h1>
<small>(Last updated %s)</small><br>
<button id="all" class="filter-btn">Show All</button>
<button id="aggregates" class="filter-btn">Show Aggregates Only</button>
<button id="entry" class="filter-btn">Show Entries Only</button>
<table id="%s" class="display"></table>
<br><br>
<a href="all_%s.jpg" style="color:#F0F0F0;">cheatsheet</a>
<script type="text/javascript" src="%s.js"></script>
<script src="cityIndex.js"></script>
<script src="counts.js"></script>
</body>
</html>
""" % (citysrc,citysrc,citysrc, update_stamp, cleanNameUnderscore(citysrc), citysrc, citysrc))

def initAnim(fname, stepsize, flag):
    with open(outdir_prefix + "/plots/" + fname + '.js', 'w+') as f:
        f.write("""
  var sliderSteps = [];
  for (i = 0; i < %d; i++) {
    sliderSteps.push({
      method: 'animate',
      label: Math.floor(10*(10 - i * %f)) / 10,
      args: [['frame' + (i)], {
        mode: 'immediate',
        transition: {duration: 0},
        frame: {duration: %d, redraw: false},
      }]
    });
  }

function bubbles(center, radius, n_points=10) {
    var step = 1 / (n_points-1)
    var x = []
    var y = []
    for (var p = 0; p < n_points; p++) {
      x.push(center[0]+radius*Math.cos(2*3.14159*step*p))
      y.push(center[1]+radius*Math.sin(2*3.14159*step*p))
    }
    return [x, y]
  }


""" % (10 / stepsize + 1, stepsize, stepsize * 1000))

    with open(outdir_prefix + "/plots/" + fname + '.html', 'w+') as f:
        f.write("""
<head>
    <!-- Load plotly.js into the DOM -->
    %s
    <script src='https://cdn.plot.ly/plotly-2.26.0.min.js'></script>
</head>

<body>
    <div id='%s'><!-- Plotly chart will be drawn inside this DIV --></div>
    <script src='%s'></script>
</body>
""" % (flag, fname, fname + '.js'))

def addFrame(fname, serieslabel, raw_country, numclicks, xdata, ydata, marker):
    with open(outdir_prefix + "/plots/" + fname + '.js', 'a') as f:
        f.write("""var %s = {
  name: '%s (%d)',
  rawname: '%s',
  x: [null,%s],
  y: [null,%s],
  mode: 'markers',
  hoverinfo: 'name',
  type: 'scatter',
  marker: {%s}
}
""" % (serieslabel, raw_country, numclicks, raw_country, ','.join([str(int(x)) for x in xdata]), ','.join([str(int(x)) for x in ydata]), marker))


def addMean(fname, xmean, ymean, xvar, yvar):
    with open(outdir_prefix + "/plots/" + fname + '.js', 'a') as f:
        f.write("""
let bubble = bubbles([%s, %s], %s)
var average = {
  name: 'average joe (1)',
  rawname: 'average joe',
            type: 'circle',
            xref: 'x',
            yref: 'y',
            x: bubble[0],
            y: bubble[1],
            opacity: 0.8,
            fillcolor: 'blue',
            line: {
                color: 'blue'
            }
}
""" % (xmean, ymean, xvar))

def finishAnim(fname, citysrc, title, countries, maxframe, stepsize):
    with open(outdir_prefix + "/plots/" + fname + '.js', 'a') as f:
        # f.write("""var traces = [ truth, average, %s]
        f.write("""var traces = [ truth, %s]
var layout = {
  xaxis: {
    range: [ 0, 1530 ],
    showgrid: false,
    zeroline: false,
    visible: false
  },
  yaxis: {
    range: [0, 900],
    showgrid: false,
    zeroline: false,
    visible: false
  },
  width: 1530,
  height: 900,
  images: [
      {
        "source": "https://geoscents.net/resources/maps/%s_terrain.png",
        "xref": "x",
        "yref": "y",
        "x": 0,
        "y": 900,
        "opacity": 0.4,
        "sizex": 1530,
        "sizey": 900,
        "sizing": "stretch",
        "layer": "below"
      }
      ],
  title:"%s",
  hovermode: 'closest',
    updatemenus: [{
      x: 0,
      y: 0,
      yanchor: 'top',
      xanchor: 'left',
      showactive: false,
      direction: 'left',
      type: 'buttons',
      pad: {t: 0, r: 0},
      buttons: [{
        method: 'animate',
        args: [null, {
          mode: 'immediate',
          fromcurrent: true,
          transition: {duration: 0},
          frame: {duration: %d, redraw: false}
        }],
        label: 'Play'
      }, {
        method: 'animate',
        args: [[null], {
          mode: 'immediate',
          transition: {duration: 0},
          frame: {duration: 0, redraw: false}
        }],
        label: 'Pause'
      }]
    }],
   // Finally, add the slider and use `pad` to position it
   // nicely next to the buttons.
    sliders: [{
      pad: {l: 0, t: 0},
      currentvalue: {
        visible: true,
        prefix: 'Time Remaining: ',
        xanchor: 'right',
        font: {size: 20, color: '#666'}
      },
      steps: sliderSteps
    }]
    };
frames = [""" % (','.join([cleanName(x) + str(maxframe) for x in sorted(countries)]), cleanName(citysrc), title, stepsize * 1000))
        for i in range(0,maxframe+1):
            # f.write("""{data: [truth,average,%s], name: "frame%d"},
            f.write("""{data: [truth,%s], name: "frame%d"},
""" % (','.join([cleanName(x) + str(i) for x in sorted(countries)]), i))

        f.write("""]
Plotly.newPlot('%s', {data: traces, layout: layout, frames: frames})

function applyZoom() {
    const scale = Math.floor(50*Math.max(0.6, Math.min(1, window.innerWidth / 1800)))/50;
    document.documentElement.style.zoom = scale;
    document.documentElement.style.MozTransform = "scale(" + scale + ")";
    document.documentElement.style.MozTransformOrigin = "0 0";
}
applyZoom();
window.addEventListener('resize', applyZoom);


""" % fname)


def nextColor(color_idx, num_colors):
    spread = 11
    g = (1 + np.cos(color_idx * spread / num_colors * 2 * np.pi)) / 2.0
    r = (1 + np.cos((color_idx * spread + num_colors / 3) / num_colors * 2 * np.pi)) / 2.0
    b = (1 + np.cos((color_idx * spread + 2 * num_colors / 3) / num_colors * 2 * np.pi)) / 2.0
    return (r,g,b,0.75)


def warnIfDatapointCountDropped():
    # If the last value in growth.csv is smaller than the second last, then post a warning to geoscents
    with open('../growth.csv', newline='') as csvfile:
        growth = csvfile.readlines()
        last_row = int(growth[-1].split(',')[-1])
        second_last_row = int(growth[-2].split(',')[-1])
        if (last_row < second_last_row):
            err = "Last stats scrape had " + str(last_row) + " datapoints, but previous one had " + str(second_last_row) + " points!"
            print(err)
            url = 'https://geoscents.net/'
            myobj = {'msg': err}
            x = requests.post(url, json = myobj, allow_redirects = True, verify = False)
            print(x.text)
        elif (last_row >= second_last_row):
            # do nothing
            print()
        else:
            err = "scrape error? Last 2 rows: " + growth[-1] + " - " + growth[-2]
            print(err)
            url = 'https://geoscents.net/'
            myobj = {'msg': err}
            x = requests.post(url, json = myobj, allow_redirects = True, verify = False)
            print(x.text)





########
# MAIN #
########

warnIfDatapointCountDropped()

pathlist = glob.glob("*.json")

sorted_countries = []
i = 0
header = ""
with open('./player_countries.csv') as fp:
    for cnt, line in enumerate(fp):
        if (cnt < 1):
            header = line.replace("[","").replace("]","").replace("\n","").split(",")
        else:
            sorted_countries.append(line)
        # if ("Total" in line.split(',')[0]):
        #     sorted_countries.append("""<tr><td> </td><td><b>""" + ','.join(line.split(',')[0:-1]) + """</b></td><td><b>""" + line.split(',')[-1] + "</b></td></tr>\n")
        # else:
        #     i = i + 1
        #     sorted_countries.append(("""<tr><td>%d.""" % i) + """</td><td>""" + ','.join(line.split(',')[0:-1]) + """</td><td>""" + line.split(',')[-1] + "</td></tr>\n")

writeIndex(header, '\n'.join(sorted_countries))
writeCss()

print('Output dir = %s' % (outdir_prefix + '/plots/'))
admin_to_country = {}
admin_to_iso2 = {}
num_colors = 49.
color_idx = 0
dpi = 250
timestep = 0.2

initCount()

_PERF_LOG = "/tmp/geoscents_perf.log"
_map_timings = []   # list of (citysrc, total_sec, agg_sec)
_t_script_start = timer()

errors = []
city_to_maps = {}

for path in pathlist:
    
    # because path is object not string
    file = str(path)
    citysrc = file.split('/')[-1].replace('.json','')
    continent_count = 0
    if (citysrc not in header):
        continue
    _t_map = timer()
    print(file)
    continent_map = mpimg.imread(outdir_prefix + '/geoscents/resources/maps/' + cleanName(citysrc) + '_terrain.png')
    writeHtml(citysrc, header[2:])
    initJs(citysrc) 
   
    with open(file) as json_file:
        aggregate_dists = {} 
        aggregate_lats = {} 
        aggregate_lons = {} 
        aggregate_times = {} 
        aggregate_player_countries = {} 
        entriesSummary = []
        continentSummary = []
        continentTrueXs = []
        continentTrueYs = []
        data = json.load(json_file)
        entry_id = 0
        made_plt = False
        for entry in data:
            # if (entry_id == 5): break # early quit
            if (verbose):
                print('%s: (%d / %d): %s' % (citysrc, entry_id, len(data), entry))
            entry_id = entry_id + 1
            if entry not in city_to_maps:
                city_to_maps[entry] = []
            if citysrc not in city_to_maps[entry]:
                city_to_maps[entry].append(citysrc)
            # Create entry for this city
            try:
                dist_data = data[entry]['dists']
                if ('iso2' not in data[entry]):
                    continue
                iso2 = data[entry]['iso2']
                continent_count = continent_count + len(dist_data)
                if ('country' not in data[entry]):
                    continue
                country = data[entry]['country']
                if trackAdmin(cleanName(citysrc), cleanName(country)) and hasattr(data[entry], 'admin'):
                    aggregate_name = cleanNameUnderscore(data[entry]['admin'])
                    admin_to_iso2[aggregate_name] = iso2
                    admin_to_country[aggregate_name] = country
                else:
                    aggregate_name = cleanNameUnderscore(country)
                    admin_to_iso2[aggregate_name] = iso2
                if (aggregate_name in aggregate_dists): 
                    aggregate_dists[aggregate_name] = aggregate_dists[aggregate_name] + dist_data
                else:
                    aggregate_dists[aggregate_name] = dist_data
                mean_dist = data[entry]['mean_dist'] if 'mean_dist' in data[entry] else 0
                std_dist = data[entry]['std_dist'] if 'std_dist' in data[entry] else 0
                outliers = [x for x in dist_data if x - mean_dist > 3 * std_dist]
                inliers = [x for x in dist_data if x - mean_dist <= 3 * std_dist]
                if (len(inliers) == 0):
                    inliers = [0]
                max_inlier = max(inliers)
                x = np.linspace(0,max_inlier,100)
                bins = plt.hist(inliers, bins=20)
                made_plt = True
                fit = stats.norm.pdf(x, mean_dist, std_dist)
                # Generate hist
                plt.plot(x,(max(bins[0]) / max(fit)) * fit)
                plt.title(entry)
                plt.xlabel('Error in km (%d outliers omitted)' % len(outliers))
                plt.ylabel('# of players')
                plt.xlim([0,max_inlier])
                fname_country = data[entry]['country'] if 'country' in data[entry] else 'unk_country'
                fname = 'entry_' + citysrc + '_' + fname_country + '_' + entry
                fname = stripSpecial(cleanNameUnderscore(fname)) + '.png'
                plt.savefig(outdir_prefix + '/plots/' + fname)
                plt.clf()
                # # Interactive plot show
                #plt.show(block=False)
                #input("Press Enter to continue...")
                #plt.close('all')


                # Save entry in table
                anim_name = 'animation_' + citysrc + '_' + cleanNameUnderscore(country) + '_' + cleanNameUnderscore(entry)
                admin = "N/A" if 'admin' not in data[entry] else data[entry]['admin']
                reghist = '<a href=\\"%s\\"><img src=\\"%s\\" class=\\"img-thumbnail\\" alt=\\"link\\" height=40px></a>' % (fname, fname)
                anim = '<a href=\\"%s\\"><img src=\\"%s\\" class=\\"img-thumbnail\\" alt=\\"link\\" height=40px></a>' % (anim_name + '.html', cleanName(citysrc) + '_terrain.png')
                link = "https://en.wikipedia.org/wiki/Special:Search?search=" + stripSpecial(entry) + "&go=Go&ns0=1" if ('wiki' not in data[entry]) else data[entry]['wiki']
                linkedCity = data[entry]['city'] if 'city' in data[entry] else "unknown_city"
                linkedEntry = '<a href=\\"%s\\">%s</a>' % (link, linkedCity) 
                flag = " " if (iso2 == 'NONE') else '<img src=\\"flags/%s.png\\" class=\\"img-thumbnail\\" style=\\"border:1px solid black;\\" alt=\\"%s\\" height=20px>' % (iso2.lower(), iso2.lower())
                bigflag = " " if (iso2.lower() == 'none') else '<img src="flags/%s.png" style="border:1px solid black;display:block;margin:0 auto" class="img-thumbnail" height=40px>' % iso2.lower()
                addJs('"Entry","' + flag + '","' + country + '","' + admin + '","' + linkedEntry + '","' + '%.1f' % mean_dist + '","' + '%.1f' % std_dist + '","' + str(len(dist_data)) + '","' + reghist + '","' + anim + '"')

                # Source image from game resources/maps now, so no need to copy here?

                # if (entry_id == 1):
                #     plt.figure(figsize=(MAP_WIDTH/dpi, MAP_HEIGHT/dpi), dpi=dpi)
                #     plt.imshow(continent_map)
                #     plt.axis('off')
                #     plt.savefig(outdir_prefix + '/plots/' + citysrc + '.jpg')
                #     plt.clf()
                #     plt.close()

                initAnim(anim_name, timestep, bigflag)
                true_x, true_y = (0,0) if ("true_lat" not in data[entry] or "true_lon" not in data[entry]) else geoToMerc(citysrc, data[entry]["true_lat"], data[entry]["true_lon"]) 
                addFrame(anim_name, "truth", "truth", 1, [true_x], [900 - true_y], 'size: 9, symbol: \'star-open\', color: \'black\'')
                continentTrueXs.append(true_x)
                continentTrueYs.append(true_y)
                if (generate_gifs):
                    # Generate animation
                    lats = data[entry]['lats']
                    lons = data[entry]['lons']
                    mean_lat = np.mean([x for x in lats if type(x) == float])
                    mean_lon = np.mean([x for x in lons if type(x) == float])
                    mean_x, mean_y = geoToMerc(citysrc, mean_lat, mean_lon) 
                    # addMean(anim_name, mean_x, 900 - mean_y, 2, 2)
                    times = data[entry]['times']
                    player_countries = data[entry]['countries']
                    tup = [[lon, time, player_country, lat] for lon, time, player_country, lat in zip(lons, times, player_countries, lats) if lat != "x"]
                    tup = list(map(list, zip(*tup)))
                    lons = tup[0]
                    times = tup[1]
                    player_countries = tup[2]
                    lats = tup[3]
                    x_by_country = {}
                    y_by_country = {}
                    if (aggregate_name in aggregate_lats): 
                        aggregate_lats[aggregate_name] = aggregate_lats[aggregate_name] + lats
                        aggregate_lons[aggregate_name] = aggregate_lons[aggregate_name] + lons
                        aggregate_times[aggregate_name] = aggregate_times[aggregate_name] + times
                        aggregate_player_countries[aggregate_name] = aggregate_player_countries[aggregate_name] + player_countries
                    else:
                        aggregate_lats[aggregate_name] = lats
                        aggregate_lons[aggregate_name] = lons
                        aggregate_lats[aggregate_name] = lats
                        aggregate_times[aggregate_name] = times
                        aggregate_player_countries[aggregate_name] = player_countries
                    all_countries = list(set(player_countries))
                    country_numclicks = {}
                    for c in all_countries:
                        country_numclicks[c] = player_countries.count(c)
                        x_by_country[c] = []
                        y_by_country[c] = []
                    frame = 0
                    for t in np.arange(10, -timestep, -timestep):
                        lowerbound = t - timestep
                        # Fetch points that fall within this step range
                        filtered = [[lat, lon, player_country] for lat,lon,player_country,stamp in zip(lats, lons, player_countries, times) if stamp > lowerbound and stamp <= t]
                        if (len(filtered) == 0):
                            filtered = [[], [], []]
                        else:
                            filtered = list(map(list, zip(*filtered)))
                        frame_lats = filtered[0]
                        frame_lons = filtered[1]
                        frame_player_countries = filtered[2]
                        for i in range(len(frame_lats)):
                            x,y = geoToMerc(citysrc, float(frame_lats[i]), float(frame_lons[i]))
                            x_by_country[frame_player_countries[i]] = x_by_country[frame_player_countries[i]] + [x]
                            y_by_country[frame_player_countries[i]] = y_by_country[frame_player_countries[i]] + [900-y]
                        for c in all_countries:
                            addFrame(anim_name, cleanName(c) + str(frame), c, country_numclicks[c], x_by_country[c], y_by_country[c], 'size: 5')
                        # Remove these processed points from our lists
                        unfiltered = [[lat, lon, player_country, stamp] for lat,lon,player_country,stamp in zip(lats, lons, player_countries, times) if stamp <= lowerbound]
                        if (len(unfiltered) == 0):
                            frame = frame + 1
                            continue;
                        unfiltered = list(map(list, zip(*unfiltered)))
                        lats = unfiltered[0]
                        lons = unfiltered[1]
                        player_countries = unfiltered[2]
                        times = unfiltered[3]
                        frame = frame + 1
                    finishAnim(anim_name, citysrc, entry, all_countries, frame - 1, timestep)


            except Exception as e: # work on python 3.x
                errors.append("problem with entry " + entry + " in " + citysrc)
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
                if hasattr(e, 'message'):
                    print(e.message)



        # Report total count for citysrc and make citysrc aggregate map
        writeCount(citysrc, continent_count)
        plt.clf()
        plt.figure(figsize=(MAP_WIDTH/dpi, MAP_HEIGHT/dpi), dpi=dpi)
        plt.imshow(continent_map)
        ax = plt.gca()
        plt.ylim([MAP_HEIGHT,0])
        plt.xlim([0,MAP_WIDTH])
        plt.title("All " + str(len(continentTrueXs)) + " entries for " + citysrc)
        plt.axis('off')
        for i in range(len(continentTrueXs)):
            x,y = continentTrueXs[i], continentTrueYs[i]
            plt.scatter([x], [y], marker='*', color='w', s = 20, edgecolors = 'black')
        plt.savefig(outdir_prefix + '/plots/all_' + citysrc + ".jpg")
        plt.clf()

        # Add aggregate for each country
        _t_agg = timer()
        if (citysrc != "Trivia"):
            entry_id = 0
            for aggregate_name in aggregate_dists:
                if (verbose):
                    print('%s: (%d / %d): %s' % (citysrc, entry_id, len(aggregate_dists), aggregate_name))
                entry_id = entry_id + 1
                try:
                    if (aggregate_name in admin_to_country):
                        country = admin_to_country[aggregate_name]
                        admin = aggregate_name
                    else:
                        country = aggregate_name
                    if (aggregate_name not in admin_to_iso2):
                        continue
                    iso2 = admin_to_iso2[aggregate_name].lower()
                    dist_data = aggregate_dists[aggregate_name]
                    mean_dist = np.mean(dist_data)
                    std_dist = np.std(dist_data)
                    outliers = [x for x in dist_data if x - mean_dist > 3 * std_dist]
                    inliers = [x for x in dist_data if x - mean_dist <= 3 * std_dist]
                    if (len(inliers) == 0):
                        inliers = [1]
                    bins = plt.hist(inliers, bins=20)
                    x = np.linspace(0,max(inliers),100)
                    fit = stats.norm.pdf(x, mean_dist, std_dist)
                    plt.plot(x,(max(bins[0]) / max(fit)) * fit)
                    plt.title('Aggregate for ' + aggregate_name)
                    plt.xlim([0,max(inliers)])
                    plt.xlabel('Error in km (%d outliers omitted)' % len(outliers))
                    plt.ylabel('# of players')
                    fname = 'country_' + citysrc + '_' + aggregate_name
                    fname = stripSpecial(cleanNameUnderscore(fname)) + ".png"
                    plt.savefig(outdir_prefix + '/plots/' + fname)
                    plt.clf()
                    reghist = '<a href=\\"%s\\"><img src=\\"%s\\" class=\\"img-thumbnail\\" alt=\\"link\\" height=40px></a>' % (fname, fname)
                    anim_name = 'animation_' + cleanNameUnderscore(citysrc) + '_' + cleanNameUnderscore(aggregate_name)
                    anim = '<a href=\\"%s\\"><img src=\\"%s\\" class=\\"img-thumbnail\\" alt=\\"link\\" height=40px></a>' % (anim_name + '.html', cleanName(citysrc) + '_terrain.png')
                    link = "https://en.wikipedia.org/wiki/Special:Search?search=" + aggregate_name + "&go=Go&ns0=1"
                    flag = " " if (iso2.lower() == 'none') else '<img src=\\"flags/%s.png\\" style=\\"border:1px solid black;\\" class=\\"img-thumbnail\\" alt=\\"%s\\" height=20px>' % (iso2, iso2)
                    bigflag = " " if (iso2.lower() == 'none') else '<img src="flags/%s.png" style="border:1px solid black;display:block;margin:0 auto" class="img-thumbnail" height=40px>' % iso2.lower()
                    if (aggregate_name in admin_to_country):
                        linkedAdmin = '<a href=\\"%s\\">%s</a>' % (link, admin)  
                        linkedCountry = country
                    else:
                        linkedAdmin = '-'
                        linkedCountry = '<a href=\\"%s\\">%s</a>' % (link, country) 
                    addJs('"Aggregate","' + flag + '","' + linkedCountry + '","' + linkedAdmin + '","-","' + '%.1f' % mean_dist + '","' + '%.1f' % std_dist + '","' + str(len(dist_data)) + '","' + reghist + '","' + anim + '"')
        
                    # Generate animation
                    if (generate_gifs):
                        initAnim(anim_name, timestep, bigflag)
                        addFrame(anim_name, "truth", "truth", 0, [], [], 'size: 8, symbol: \'star-open\', color: \'black\'')
                        lats = aggregate_lats[aggregate_name]
                        lons = aggregate_lons[aggregate_name]
                        mean_lat = np.mean([x for x in lats if type(x) == float])
                        mean_lon = np.mean([x for x in lons if type(x) == float])
                        mean_x, mean_y = geoToMerc(citysrc, mean_lat, mean_lon) 
                        # addMean(anim_name, mean_x, 900 - mean_y, 2, 2)
                        times = aggregate_times[aggregate_name]
                        player_countries = aggregate_player_countries[aggregate_name]
                        lons = [l for l,x in zip(lons,lats) if x != "x"]
                        times = [l for l,x in zip(times,lats) if x != "x"]
                        player_countries = [l for l,x in zip(player_countries,lats) if x != "x"]
                        lats = [x for x in lats if x != "x"]
                        x_by_country = {}
                        y_by_country = {}
                        all_countries = []
                        country_numclicks = {}
                        for c in player_countries:
                            if (c not in all_countries):
                                all_countries.append(c)
                                country_numclicks[c] = player_countries.count(c)
                                x_by_country[c] = []
                                y_by_country[c] = []
                        frame = 0
                        for t in np.arange(10, -timestep, -timestep):
                            lowerbound = t - timestep
                            frame_lats = [x for x,stamp in zip(lats, times) if stamp > lowerbound and stamp <= t]
                            frame_lons = [x for x,stamp in zip(lons, times) if stamp > lowerbound and stamp <= t]
                            frame_player_countries = [x for x,stamp in zip(player_countries, times) if stamp > lowerbound and stamp <= t]
                            for i in range(len(frame_lats)):
                                x,y = geoToMerc(citysrc, float(frame_lats[i]), float(frame_lons[i]))
                                x_by_country[frame_player_countries[i]] = x_by_country[frame_player_countries[i]] + [x]
                                y_by_country[frame_player_countries[i]] = y_by_country[frame_player_countries[i]] + [900-y]
                            for c in all_countries:
                                addFrame(anim_name, cleanName(c) + str(frame), c, country_numclicks[c], x_by_country[c], y_by_country[c], 'size: 5')
                            frame = frame + 1
                        finishAnim(anim_name, citysrc, aggregate_name, all_countries, frame - 1, timestep)

                            
                except Exception as e: # work on python 3.x
                    errors.append("problem with aggregate " + aggregate + " in " + citysrc)
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print(exc_type, fname, exc_tb.tb_lineno)
                    if hasattr(e, 'message'):
                        print(e.message)



    _elapsed_map = timer() - _t_map
    _elapsed_agg = timer() - _t_agg
    _map_timings.append((citysrc, _elapsed_map, _elapsed_agg))
    print('[timing] %s: %.1fs total (agg: %.1fs, entries: %.1fs)' % (
        citysrc, _elapsed_map, _elapsed_agg, _elapsed_map - _elapsed_agg))
    finishJs(citysrc)

for x in errors:
    print(x)

writeCityIndex(city_to_maps)

_perf_lines = ['  --- plot_hist.py per-map timing (slowest first) ---',
               '  %-30s %7s  %7s  %7s' % ('Map', 'Total', 'Entries', 'Agg')]
for _n, _t, _ta in sorted(_map_timings, key=lambda x: -x[1]):
    _perf_lines.append('  %-30s %6.1fs  %6.1fs  %6.1fs' % (_n, _t, _t - _ta, _ta))
_perf_lines.append('  %-30s %6.1fs' % ('TOTAL script', timer() - _t_script_start))
_perf_str = '\n'.join(_perf_lines) + '\n'
print(_perf_str)
with open(_PERF_LOG, 'a') as _pf:
    _pf.write(_perf_str)

