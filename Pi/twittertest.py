#!/usr/bin/env python
# encoding: utf-8
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

stuff = api.user_timeline(screen_name = 'iss101', count = 1, include_rts = True)

test = ""

for status in stuff:
    print status.text
    test = (status.text)

emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                           "]+", flags=re.UNICODE)
print(emoji_pattern.sub(r'', test)) # no emoji
