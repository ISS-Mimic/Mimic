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

for status in stuff:
    latest_tweet = status.full_text

EVnames = []
EVpics = []
index = 0

if ("EVA BEGINS" in latest_tweet) and latest_tweet.count('@') == 2:
    crew_mention = True
    while index < len(latest_tweet):
        index = latest_tweet.find('@',index)
        if index == -1:
            break
        EVnames.append(str(latest_tweet[index:]))
        EVpics.append("")
        index += 1
    count = 0

    while count < len(EVnames):
        EVnames[count] = (EVnames[count].split('@')[1]).split(' ')[0]
        count += 1
    count = 0

    while count < len(EVnames):
        EVpics[count] = str(api.get_user(EVnames[count]).profile_image_url)
        EVnames[count] = str(api.get_user(EVnames[count]).name)
        print EVpics[count]
        EVpics[count] = EVpics[count].replace("_normal","_bigger")
        print EVpics[count]
        count += 1

