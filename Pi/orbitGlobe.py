# retrieve the TLE for the ISS
import urllib.request
import numpy as np
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import ephem
import os
import os.path as op

mimic_directory = op.abspath(op.join(__file__, op.pardir, op.pardir, op.pardir))

url = "https://www.celestrak.com/NORAD/elements/stations.txt"
response = urllib.request.urlopen(url)
data = response.read().decode('utf-8')
lines = data.strip().split('\n')

for i in range(len(lines)):
    if "ISS (ZARYA)" in lines[i]:
        iss_tle = lines[i] + '\n' + lines[i+1] + '\n' + lines[i+2]
        break

# create an ephem observer for the ISS using the TLE
iss = ephem.readtle(iss_tle.split('\n')[0], iss_tle.split('\n')[1], iss_tle.split('\n')[2])

# get the current location of the ISS from ephem
iss.compute()
latitude = np.rad2deg(iss.sublat)
longitude = np.rad2deg(iss.sublong)

# calculate the orbital path of the ISS for the next hour
orbit_lat = []
orbit_lon = []
for t in range(95):
    iss.compute(ephem.now() + t*ephem.minute)
    orbit_lat.append(np.rad2deg(iss.sublat))
    orbit_lon.append(np.rad2deg(iss.sublong))

def plotEarthColor():
    # create a basemap of the earth with the Orthographic projection
    fig = plt.figure(figsize=(8, 8))
    m = Basemap(projection='ortho', lat_0=latitude, lon_0=longitude, resolution=None)
    m.bluemarble(scale=0.5)

    # plot the groundtrack of the ISS
    m.plot(orbit_lon, orbit_lat, latlon=True, color='green')

    # plot the current location of the ISS
    x, y = m(longitude, latitude)
    m.plot(x, y, 'ro', markersize=10)

    # draw a grid of latitudes and longitudes on the map
    m.drawmeridians(np.arange(0, 360, 30), color='white')
    m.drawparallels(np.arange(-90, 90, 30), color='white')

    # show the plot
    #plt.show()
    plt.savefig(mimic_directory + '/Mimic/Pi/imgs/orbit/globe.png',transparent = True)

def plotEarthNoColor():
    # create a basemap of the earth
    fig = plt.figure(figsize=(8, 8))
    m = Basemap(projection='ortho', lat_0=latitude, lon_0=longitude)
    m.shadedrelief()

    # plot the groundtrack of the ISS
    m.plot(orbit_lon, orbit_lat, latlon=True, color='green', linewidth=2)

    # plot the current location of the ISS
    x, y = m(longitude, latitude)
    m.plot(x, y, 'ro', markersize=20)

    # add coastlines, countries, and gridlines
    m.drawcoastlines()
    m.drawcountries()
    #m.drawparallels(np.arange(-90., 120., 30.), labels=[1, 0, 0, 0])
    #m.drawmeridians(np.arange(0., 420., 60.), labels=[0, 0, 0, 1])

    # show the plot
    plt.savefig(mimic_directory + '/Mimic/Pi/imgs/orbit/globe.png', dpi=100, transparent = True)

plotEarthNoColor()
