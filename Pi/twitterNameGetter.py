#!/usr/bin/env python
# encoding: utf-8
import json
import re
import tweepy #https://github.com/tweepy/tweepy

#Twitter API credentials
consumer_key = "qsaZuBudT7HRaXf4JU0x0KtML"
consumer_secret = "C6hpOGEtzTc9xoCeABgEnWxwWXjp3qOIpxrNiYerCoSGXZRqEd"
access_key = "896619221475614720-MBUhORGyemI4ueSPdW8cAHJIaNzgdr9"
access_secret = "Lu47Nu4eQrtQI1vmKUIMWTQ419CmEXSZPVAyHb8vFJbTu"

#Twitter only allows access to a users most recent 3240 tweets with this method
#authorize twitter, initialize tweepy
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_key, access_secret)
api = tweepy.API(auth)
stuff = api.user_timeline(screen_name = 'iss_mimic', count = 1, include_rts = True, tweet_mode = 'extended')
#stuff = api.get_status(909345339391561729)

for status in stuff:
    parsingtext = status.full_text

storage = []
index = 0
while index < len(parsingtext):
    index = parsingtext.find('@',index)
    if index == -1:
        break
    storage.append(str(parsingtext[index:]))
    index += 1

count = 0
while count < len(storage):
    storage[count] = (storage[count].split('@')[1]).split(' ')[0]
    count += 1

count = 0
while count < len(storage):
    storage[count] = str(api.get_user(storage[count]).name)
    count += 1

print storage

#for friend in tweepy.Cursor(api.friends, screen_name="NASA_Astronauts").items():
#    print friend.screen_name
#    print friend.name
#    print friend.user.name
