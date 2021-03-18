import json
import math
import pickle
import ephem
import numpy as np
from urllib.parse import unquote_plus
from scipy.spatial import distance_matrix
from scipy.sparse.csgraph import dijkstra
from skyfield.api import EarthSatellite, load, Topos
from flask import Blueprint, render_template, Response

main = Blueprint('main', __name__, template_folder='templates', static_url_path='', static_folder='static')

ts = load.timescale()
with open('starlink/starlink_tle.pickle', 'rb') as fp:
    ephems = pickle.load(fp)
sats = []
for sat in ephems:
    if sat:
        tle = sat.decode().split('\r\n')
        if len(tle) < 3:
            continue
        if tle[0].find("STARLINK") < 0:
            continue
        s1 = EarthSatellite(tle[1], tle[2], tle[0].strip())
        latlng = s1.at(ts.now()).subpoint()
        if math.isnan(latlng.longitude.degrees) or math.isnan(latlng.latitude.degrees):
            continue
        sats.append(s1)


@main.route('/', methods=["GET"])
def index():
    return render_template('index.html', zoom=8.5, center={"lat": -27.4, "lng": 153.4})


@main.route('/sats.geojson', methods=["GET"])
def get_satellites():
    geojson = {
        "type": "FeatureCollection",
        "features": [],
    }
    for sat in sats:
        if sat.name.find("STARLINK") < 0:
            continue
        pos = sat.at(ts.now())
        latlng = pos.subpoint()
        if math.isnan(latlng.longitude.degrees) or math.isnan(latlng.latitude.degrees):
            continue
        feature = {"type": "Feature",
                   "properties": {"name": sat.name},
                   "geometry": {
                       "type": "Point",
                       "coordinates": [latlng.longitude.degrees, latlng.latitude.degrees],
                   }}
        geojson["features"].append(feature)
    return Response(json.dumps(geojson), mimetype="application/json")


@main.route('/orbits.geojson', methods=["GET"])
def get_orbits():
    geojson = {
        "type": "FeatureCollection",
        "features": [],
    }
    for sat in sats:
        if sat.name.find("STARLINK") < 0:
            continue
        feature = {"type": "Feature",
                   "properties": {"name": sat.name},
                   "geometry": {
                       "type": "LineString",
                       "coordinates": [],
                   }}
        times = ts.tt_jd(np.arange(ts.now().tt - 0.0012, ts.now().tt + 0.0012, 0.0002))
        pos = sat.at(times)
        latlng = pos.subpoint()
        if np.isnan(latlng.longitude.degrees).any() or np.isnan(latlng.latitude.degrees).any():
            continue
        feature["geometry"]["coordinates"] = list(
            zip(np.unwrap(latlng.longitude.degrees), np.unwrap(latlng.latitude.degrees)))
        geojson["features"].append(feature)
    return Response(json.dumps(geojson), mimetype="application/json")


@main.route('/path/<city1>/<city2>/', methods=["GET"])
def get_path(city1, city2):
    try:
        obs1 = ephem.city(unquote_plus(city1))
    except:
        obs1 = ephem.city(unquote_plus('London'))
    try:
        obs2 = ephem.city(unquote_plus(city2))
    except:
        obs2 = ephem.city(unquote_plus('New York'))
    top1 = Topos(latitude_degrees=obs1.lat * 180 / math.pi, longitude_degrees=obs1.long * 180 / math.pi)
    top2 = Topos(latitude_degrees=obs2.lat * 180 / math.pi, longitude_degrees=obs2.long * 180 / math.pi)
    pos_up = top1.at(ts.now())
    pos_down = top2.at(ts.now())
    up = (-10, 10e10)
    down = (-10, 10e10)

    # Create a position matrix of the satellites then calculate the distance matrix
    X = []
    latlng = []
    for i, sat in enumerate(sats):
        pos = sat.at(ts.now())
        ll = pos.subpoint()
        latlng.append((ll.longitude.degrees, ll.latitude.degrees))
        X.append(pos.position.km)
        dup = np.linalg.norm((pos - pos_up).position.km)

        # Check if the current satellite is closest to the ground stations
        if dup < up[1]:
            up = (i, dup)
        ddown = np.linalg.norm((pos - pos_down).position.km)
        if ddown < down[1]:
            down = (i, ddown)
    D = distance_matrix(X, X)
    D[D > 1500] = 1e10#float('inf')

    # shortest_path has the choice of Floyd-Warshall, Dijkstra's with FIbonacci heaps
    #   Bellman-Ford and Johnson's
    dists, pred = dijkstra(D, directed=False, indices=up[0], return_predecessors=True)
    city1_ll = pos_up.subpoint()
    city2_ll = pos_down.subpoint()
    geojson = {
        "type": "FeatureCollection",
        "features": [{"type": "Feature",
                      "properties": {"name": f"{city1} to {city2}"},
                      "geometry": {
                          "type": "LineString",
                          "coordinates": [(city2_ll.longitude.degrees, city2_ll.latitude.degrees)],
                      }}]
    }
    path = geojson["features"][0]["geometry"]["coordinates"]
    total_distance = down[1] + dists[down[0]] + up[1]
    geojson["features"][0]["properties"]["distance"] = total_distance*1.0
    geojson["features"][0]["properties"]["time"] = 2*total_distance/ephem.c*1000*1000

    # Follow the indices in the predecessors array to build up the path LineString
    i = down[0]
    path.append(latlng[i])
    while i != up[0]:
        i = pred[i]
        path.append(latlng[i])
    path.append([city1_ll.longitude.degrees, city1_ll.latitude.degrees])
    return Response(json.dumps(geojson), mimetype="application/json")
