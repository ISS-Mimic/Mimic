import re
import urllib2
from bs4 import BeautifulSoup

eva_url = 'http://spacefacts.de/eva/e_eva_az.htm'
soup = BeautifulSoup(urllib2.urlopen(eva_url), 'html.parser')

lastname = "Hei"
firstname = "Mark"
print "-------"
test = soup.find_all("td")
for tag in test:
    if lastname in tag.text:
        if firstname in tag.find_next_sibling("td").text:
            print tag
            numEVAs = tag.find_next_sibling("td").find_next_sibling("td").find_next_sibling("td").text
            EVAtime_hours = int(tag.find_next_sibling("td").find_next_sibling("td").find_next_sibling("td").find_next_sibling("td").text)
            EVAtime_minutes = int(tag.find_next_sibling("td").find_next_sibling("td").find_next_sibling("td").find_next_sibling("td").find_next_sibling("td").text)

print "-------"

print numEVAs
EVAtime_minutes += (EVAtime_hours * 60)
print EVAtime_minutes
