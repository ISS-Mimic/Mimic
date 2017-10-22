import tweepy
import xml.etree.ElementTree as etree

# Twitter API credentials
consumerKey = ''
consumerSecret = ''
accessToken = ''
accessTokenSecret = ''

# Retrieving key and tokens used for 0Auth
tree = etree.parse('../TwitterKeys.xml')
root = tree.getroot()
for child in root:
    if child.tag == 'ConsumerKey' and child.text is not None:
        consumerKey = child.text
        print("Consumer Key: " + consumerKey)
    elif child.tag == 'ConsumerSecret' and child.text is not None:
        consumerSecret = child.text
        print("Consumer Secret: " + consumerSecret)
    elif child.tag == 'AccessToken':
        accessToken = child.text
        print("Access Token: " + accessToken)
    elif child.tag == 'AccessTokenSecret':
        accessTokenSecret = child.text
        print("Access Token Secret: " + accessTokenSecret)
    else:
        print("Warning: Unknown or Empty element: " + child.tag)
        print(" Twitter fetching may not work.")

#OAuth process, using the keys and tokens
auth = tweepy.OAuthHandler(consumerKey, consumerSecret)
auth.set_access_token(accessToken, accessTokenSecret)

# Creation of the actual interface, using authentication
api = tweepy.API(auth)

# Testing your account
api.update_status('Hello Python Central!')
print("Check your twitter page for the status \"Hello Python Central!\"")

# Testing retrieve from mimic twitter.
#   comment out line 38 before uncommenting the following.
#stuff = api.user_timeline(screen_name = 'iss_mimic', count = 1, include_rts = True, tweet_mode = 'extended')
#print(stuff)
