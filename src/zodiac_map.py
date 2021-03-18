from typing import Dict, List

import datetime as dt
import pytz
import subprocess
import numpy as np
import drawSvg as draw

import ephem
from skyfield.api import Star, load, Topos
from skyfield.data import hipparcos, stellarium
from skyfield.projections import build_stereographic_projection


def constellation_center(edges, stars):
    star_numbers = set()
    for edge in edges:
        star_numbers.add(edge[0])
        star_numbers.add(edge[1])
    xy = stars[['x', 'y']].loc[star_numbers].values
    return xy.mean(0)


eph = load('../data/de421.bsp')
sun = eph['sun']
earth = eph['earth']

# The Hipparcos mission provides our star catalog. hipparcos.URL
with load.open('../data/hip_main.dat.gz') as f:
    stars = hipparcos.load_dataframe(f)

# And the constellation outlines come from Stellarium.  We make a list
# of the stars at which each edge stars, and the star at which each edge
# ends.

# url = ('https://raw.githubusercontent.com/Stellarium/stellarium/master'
#       '/skycultures/western_SnT/constellationship.fab')

with load.open('../data/constellationship.fab') as f:
    constellations = stellarium.parse_constellations(f)

zodiac: List[str] = ['Aqr', 'Cap', 'Sgr', 'Oph', 'Ari', 'Tau', 'Lib', 'Sco', 'Psc', 'Gem', 'Cnc', 'Leo', 'Vir', 'Ori', 'Cru']
symbols: Dict[str, str] = {
    'mercury': '☿',
    'venus': '♀',
    'mars': '♂',
    'jupiter': '♃',
    'saturn': 'I',
    'Aqr': '♒',
    'Cap': '♑',
    'Sgr': '♐',
    'Oph': '⛎',
    'Ari': '♈',
    'Tau': '♉',
    'Lib': '♎',
    'Sco': '♏',
    'Psc': '♓',
    'Gem': '♊',
    'Cnc': '♋',
    'Leo': '♌',
    'Vir': '♍',
    'Ori': '⚭',
    'Cru': '†',
}

year = 2020
month = 3
day = 16
hour = 20
minute = 42
time = dt.datetime(year, month, day, hour, minute)
tz = pytz.timezone('Australia/Brisbane')
time_tz = tz.localize(time)
ts = load.timescale()
gmt = pytz.timezone('GMT+0')
time_gmt = time_tz.astimezone(gmt)
t = ts.utc(time_gmt.year, time_gmt.month, time_gmt.day, time_gmt.hour, time_gmt.minute)
brisbane = ephem.city('Brisbane')
bris = earth + Topos(latitude_degrees=brisbane.lat * 180 / 3.14, longitude_degrees=brisbane.long * 180 / 3.14)
center = earth.at(t).observe(bris)
projection = build_stereographic_projection(center)
field_of_view_degrees = 55.0
limiting_magnitude = 4.0
star_positions = earth.at(t).observe(Star.from_dataframe(stars))
stars['x'], stars['y'] = projection(star_positions)
edges = [edge for name, edges in constellations for edge in edges if name in zodiac]
names = [(name, constellation_center(edges, stars)) for name, edges in constellations if name in zodiac]
edges_star1 = [star1 for star1, star2 in edges]
edges_star2 = [star2 for star1, star2 in edges]
xy1 = stars[['x', 'y']].loc[edges_star1].values
xy2 = stars[['x', 'y']].loc[edges_star2].values
lines_xy = np.rollaxis(np.array([xy1, xy2]), 1)
constellation_stars = np.unique(np.vstack((xy1, xy2)), axis=0)

bright_stars = (stars.magnitude <= limiting_magnitude)
# remove constellation stars
# bright_stars[edges_star1] = False
# bright_stars[edges_star2] = False
# select all constellation stars
bright_stars[edges_star1] = True
bright_stars[edges_star2] = True


moon = eph['moon']
planets = {
    'mercury': {'ephemeris': eph['mercury']},
    'venus': {'ephemeris': eph['venus']},
    'mars': {'ephemeris': eph['mars']},
    'jupiter': {'ephemeris': eph['jupiter barycenter']},
    'saturn': {'ephemeris': eph['saturn barycenter']},
}
sun_position = earth.at(t).observe(sun)
sun_x, sun_y = projection(sun_position)
moon_position = earth.at(t).observe(moon)
moon_x, moon_y = projection(moon_position)
for planet_name in planets:
    planet = planets[planet_name]
    planet['position'] = earth.at(t).observe(planet['ephemeris'])
    planet['x'], planet['y'] = projection(planet['position'])

angle = np.pi - 3 * field_of_view_degrees / 360.0 * np.pi
limit = np.sin(angle) / (1.0 - np.cos(angle))

canvas_size = 400
canvas_active = 370
scale = canvas_active / 2
magnitude = stars['magnitude'][bright_stars]
sel_1 = magnitude < 3.0
sel_2 = magnitude < 2.0
star_sizes = np.ones(magnitude.shape) * 1
star_sizes[sel_1] = 1.2
star_sizes[sel_2] = 1.5

main_drawing = draw.Drawing(canvas_size, canvas_size, origin='center')
d = draw.Drawing(canvas_size, canvas_size, origin='center')
for star in zip(stars['x'][bright_stars], stars['y'][bright_stars], star_sizes):
    if (-limit < star[0] < limit) and (-limit < star[1] < limit):
        d.append(draw.Circle(star[0]/limit * scale, star[1]/limit * scale, star[2], fill='black', stroke_width=0))
        main_drawing.append(draw.Circle(star[0]/limit * scale, star[1]/limit * scale, star[2], fill='black', stroke_width=0))
if (-limit < sun_x < limit) and (-limit < sun_y < limit):
    d.append(draw.Circle(sun_x/limit * scale, sun_y/limit * scale, 20, fill='black', stroke_width=0))
    main_drawing.append(draw.Circle(sun_x/limit * scale, sun_y/limit * scale, 20, fill='black', stroke_width=0))

d.saveSvg('../assets/stars.svg')

d = draw.Drawing(canvas_size, canvas_size, origin='center')
if (-limit < moon_x < limit) and (-limit < moon_y < limit):
    d.append(draw.Circle(moon_x/limit * scale, moon_y/limit * scale, 20, fill='black', stroke_width=0))
    main_drawing.append(draw.Circle(moon_x/limit * scale, moon_y/limit * scale, 20, fill='black', stroke_width=0))
d.saveSvg('moon.svg')

d = draw.Drawing(canvas_size, canvas_size, origin='center')
for star in constellation_stars:
    if (-limit < star[0] < limit) and (-limit < star[1] < limit):
        d.append(draw.Circle(star[0]/limit * scale, star[1]/limit * scale, 3, fill='black', stroke_width=0))
d.saveSvg('../assets/constellation_stars.svg')

d = draw.Drawing(canvas_size, canvas_size, origin='center')
for planet_name in planets:
    planet = planets[planet_name]
    if (-limit < planet['x'] < limit) and (-limit < planet['y'] < limit):
        d.append(draw.Text(symbols[planet_name], 40, scale * planet['x']/limit, scale * planet['y']/limit, fill='black'))
        main_drawing.append(draw.Text(symbols[planet_name], 40, scale * planet['x'/limit], scale * planet['y']/limit, fill='black'))
d.saveSvg('../assets/planets.svg')
# subprocess.run(
#     ['inkscape', '--without-gui', '--file=planets.svg', '--export-text-to-path', '--export-plain-svg=planets.svg'])

d = draw.Drawing(canvas_size, canvas_size, origin='center')
for text in names:
    if (-limit < text[1][0] < limit) and (-limit < text[1][1] < limit):
        d.append(draw.Text(symbols[text[0]], 20, scale * text[1][0], scale * text[1][1], fill='black'))
        #main_drawing.append(draw.Text(symbols[text[0]], 20, scale * text[1][0], scale * text[1][1], fill='black'))
d.saveSvg('../assets/constellation_names.svg')
# subprocess.run(['inkscape', '--without-gui', '--file=constellation_names.svg', '--export-text-to-path',
#                 '--export-plain-svg=constellation_names.svg'])

d = draw.Drawing(canvas_size, canvas_size, origin='center')
for line in lines_xy:
    if (-limit < line[0, 0] < limit) and (-limit < line[0, 1] < limit) and (-limit < line[1, 0] < limit) and (
            -limit < line[1, 1] < limit):
        d.append(draw.Line(*(line.flatten()/limit * scale), stroke='black', stroke_width=1, fill='black'))
        main_drawing.append(draw.Line(*(line.flatten()/limit * scale), stroke='black', stroke_width=1, fill='black'))
d.saveSvg('../assets/constellation_lines.svg')

d = draw.Drawing(canvas_size, canvas_size, origin='center')
d.append(draw.Lines(-canvas_size/2, -canvas_size/2, -canvas_size/2, canvas_size/2, canvas_size/2, canvas_size/2,
                    canvas_size/2, -canvas_size/2, -canvas_size/2, -canvas_size/2, stroke='black',
                    stroke_width=3, fill='black'))
main_drawing.append(draw.Lines(-canvas_size/2, -canvas_size/2, -canvas_size/2, canvas_size/2, canvas_size/2, canvas_size/2,
                    canvas_size/2, -canvas_size/2, -canvas_size/2, -canvas_size/2, stroke='black',
                    stroke_width=3, fill='black'))
d.saveSvg('../assets/border.svg')

main_drawing.setPixelScale(1)
main_drawing.saveSvg('../assets/main.svg')
