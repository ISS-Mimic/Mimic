import urllib2
from bs4 import BeautifulSoup
import ephem
import datetime

nasaissurl = 'http://spaceflight.nasa.gov/realdata/sightings/SSapplications/Post/JavaSSOP/orbit/ISS/SVPOST.html'
soup = BeautifulSoup(urllib2.urlopen(nasaissurl), 'html.parser')
body = soup.find_all("pre")
index = 0
firstTLE = False

results = []
for tag in body:
    if "ISS" in tag.text:
        results
