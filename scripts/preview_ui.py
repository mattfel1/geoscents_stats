#!/usr/bin/env python3
"""
Quick UI preview for plot_hist.py cosmetic changes.
Generates a self-contained /tmp/gs_preview.html — open it in any browser.
CSS/HTML here should mirror writeCss() / writeIndex() in plot_hist.py.
"""

OUT = '/tmp/gs_preview.html'

FAKE_MAPS = ['World', 'Europe', 'N. America', 'S. America', 'Africa', 'Asia',
             'Oceania', 'Trivia', 'United States', 'United Kingdom', 'France',
             'Germany', 'Japan', 'Brazil', 'Australia']

map_names_js = '[' + ','.join(['"' + m + '"' for m in FAKE_MAPS]) + ']'

html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>GeoScents UI Preview</title>
<style>
body { font-family: sans-serif; }

.room-btn {
    cursor: pointer;
    border: 1px solid #333;
    width: 120px;
    padding: 2px 2px;
    margin: 3px 3px;
    font-size: 16px;
    background: #a9e7f9;
    background: linear-gradient(to bottom, #a9e7f9 0%%, #77d3ef 4%%, #05abe0 100%%);
    border-radius: 2px;
    box-shadow: 0 0 4px rgba(0,0,0,0.3);
}

.lobby-btn {
    cursor: pointer;
    border: 1px solid #333;
    padding: 2px 2px;
    margin: 3px 3px;
    font-size: 16px;
    background: #ffcccc;
    background: linear-gradient(to bottom, #ffcccc 0%%, #ff9999 4%%, #ff6666 100%%);
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
    background: #ffe200;
    background: linear-gradient(to bottom, #ffe200 0%%, #dbc300 4%%, #bda800 100%%);
    border-radius: 2px;
    box-shadow: 0 0 4px rgba(0,0,0,0.3);
}

.map-search-wrapper {
    position: relative;
    display: block;
    margin: 10px 6px;
}

.map-search-inner {
    display: flex;
    align-items: stretch;
    width: 420px;
}

#map-search {
    flex: 1;
    padding: 6px 10px;
    font-size: 16px;
    border: 1px solid #333;
    border-right: none;
    border-radius: 2px 0 0 2px;
    box-sizing: border-box;
    outline: none;
}

#map-search-btn {
    cursor: pointer;
    border: 1px solid #333;
    padding: 2px 14px;
    font-size: 16px;
    background: linear-gradient(to bottom, #a9e7f9 0%%, #77d3ef 4%%, #05abe0 100%%);
    border-radius: 0 2px 2px 0;
    box-shadow: 0 0 4px rgba(0,0,0,0.3);
    white-space: nowrap;
}

.map-results {
    position: absolute;
    top: 100%%;
    left: 0;
    width: 100%%;
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

.map-result-item:hover, .map-result-selected { background: #a9e7f9; }

.map-result-count { color: #666; font-size: 12px; }
.map-result-city  { color: #888; font-size: 12px; font-style: italic; }
</style>
</head>
<body>
<button class="lobby-btn">Back to Game</button>
<button class="special-room-btn">Home</button>
<div class="map-search-wrapper">
    <div class="map-search-inner">
        <input type="text" id="map-search" placeholder="Search GeoScents maps &amp; cities..." autocomplete="off">
        <button id="map-search-btn">Go</button>
    </div>
    <div id="map-results" class="map-results" style="display:none;"></div>
</div>
<script>
var mapNames = %(map_names_js)s;
function appendMapItem(results, name) {
    var div = document.createElement('div');
    div.className = 'map-result-item';
    div.innerHTML = name + ' <span class="map-result-count">(1,234 clicks)</span>';
    div.onclick = function() { alert('Would navigate to: ' + name); };
    results.appendChild(div);
}
function renderMapList(query) {
    var results = document.getElementById('map-results');
    var q = (query || '').toLowerCase().trim();
    results.innerHTML = '';
    mapNames.forEach(function(name) {
        if (!q || name.toLowerCase().indexOf(q) !== -1)
            appendMapItem(results, name);
    });
    results.style.display = results.children.length ? 'block' : 'none';
}
var searchEl = document.getElementById('map-search');
var selectedIdx = -1;
function setSelected(idx) {
    var items = document.querySelectorAll('#map-results .map-result-item');
    items.forEach(function(el, i) { el.classList.toggle('map-result-selected', i === idx); });
    if (items[idx]) items[idx].scrollIntoView({ block: 'nearest' });
    selectedIdx = idx;
}
searchEl.addEventListener('input', function() { selectedIdx = -1; renderMapList(this.value); });
searchEl.addEventListener('focus', function() { renderMapList(this.value); });
searchEl.addEventListener('keydown', function(e) {
    var items = document.querySelectorAll('#map-results .map-result-item');
    if (!items.length) return;
    if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelected(Math.min(selectedIdx + 1, items.length - 1));
    } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelected(Math.max(selectedIdx - 1, 0));
    } else if (e.key === 'Enter') {
        if (selectedIdx >= 0 && items[selectedIdx]) items[selectedIdx].click();
        else if (items[0]) items[0].click();
    } else if (e.key === 'Escape') {
        document.getElementById('map-results').style.display = 'none';
        selectedIdx = -1;
    }
});
document.getElementById('map-search-btn').addEventListener('click', function() {
    var first = document.querySelector('#map-results .map-result-item');
    if (first) { first.click(); } else { renderMapList(searchEl.value); searchEl.focus(); }
});
document.addEventListener('click', function(e) {
    if (!e.target.closest('.map-search-wrapper')) {
        document.getElementById('map-results').style.display = 'none';
        selectedIdx = -1;
    }
});
</script>
</body>
</html>
""" % {'map_names_js': map_names_js}

with open(OUT, 'w') as f:
    f.write(html)

print('Preview written to ' + OUT)
print('Open with:  explorer.exe ' + OUT)
