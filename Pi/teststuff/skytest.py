from skyfield import api
from datetime import datetime
ts = api.load.timescale()

sats = api.load.tle('https://celestrak.com/NORAD/elements/stations.txt')
sats2 = api.load.tle('https://celestrak.com/NORAD/elements/tdrss.txt')
s1 = sats['ISS (ZARYA)']
s2 = sats2['TDRS 10']

while True:
    t = ts.now()
    pos1 = s1.at(t)
    pos2 = s2.at(t)
    print(pos1.separation_from(pos2))
    
