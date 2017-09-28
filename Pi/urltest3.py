import urllib2
from bs4 import BeautifulSoup

nasaissurl = 'http://spaceflight.nasa.gov/realdata/sightings/SSapplications/Post/JavaSSOP/orbit/ISS/SVPOST.html'
#TLE = BeautifulSoup(urllib2.urlopen(nasaissurl), 'html.parser')
soup = BeautifulSoup(open('./EVA.html'), 'html.parser')

name = "Acaba"

numEVAs = soup.find("td", text=name).find_next_sibling("td").find_next_sibling("td").find_next_sibling("td").text
EVAtime_hours = soup.find("td", text=name).find_next_sibling("td").find_next_sibling("td").find_next_sibling("td").find_next_sibling("td").text
EVAtime_minutes = soup.find("td", text=name).find_next_sibling("td").find_next_sibling("td").find_next_sibling("td").find_next_sibling("td").find_next_sibling("td").text

print numEVAs
print EVAtime_hours
print EVAtime_minutes
