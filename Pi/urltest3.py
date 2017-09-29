import urllib2
from bs4 import BeautifulSoup

eva_url = 'http://spacefacts.de/eva/e_eva_az.htm'
soup = BeautifulSoup(urllib2.urlopen(eva_url), 'html.parser')

name = "Hei"

print soup.find("td", text=name)

if str(soup.find("td", text=name)) == "None":
    numEVAs = 0
    EVAtime_hours = 0
    EVAtime_minutes = 0
else:
    numEVAs = soup.find("td", text=name).find_next_sibling("td").find_next_sibling("td").find_next_sibling("td").text
    EVAtime_hours = int(soup.find("td", text=name).find_next_sibling("td").find_next_sibling("td").find_next_sibling("td").find_next_sibling("td").text)
    EVAtime_minutes = int(soup.find("td", text=name).find_next_sibling("td").find_next_sibling("td").find_next_sibling("td").find_next_sibling("td").find_next_sibling("td").text)

print numEVAs
EVAtime_minutes += (EVAtime_hours * 60)
print EVAtime_minutes
