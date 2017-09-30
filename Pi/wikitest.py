import wikipedia

#print wikipedia.summary("Peggy Whitson")

bio = "http://en.wikipedia.org/wiki/Thomas_Pesquet"

reduced = bio.split("/")[-1]

print reduced

wikipage = wikipedia.page(str(reduced))
count = 0
while count < len(wikipage.images):
    print wikipage.images[count]
    count +=1
#print wikipage.images
