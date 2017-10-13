import kivy
import urllib2
from bs4 import BeautifulSoup
from calendar import timegm
import datetime
import os
import sys
import json
import sqlite3
import serial
import time
import sched, time
import smbus
import math
import random
import time
from threading import Thread
import re
from Naked.toolshed.shell import execute_js, muterun_js
from kivy.garden.gauge import Gauge
import os
import signal
import multiprocessing, signal
from kivy.animation import Animation
from kivy.uix.behaviors.button import ButtonBehavior
from kivy.uix.popup import Popup 
from kivy.uix.button import Button
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.base import runTouchApp
from kivy.clock import Clock
from kivy.properties import ListProperty
from kivy.properties import ObjectProperty
from kivy.properties import NumericProperty
from kivy.vector import Vector
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.floatlayout import FloatLayout
from kivy.event import EventDispatcher
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.stacklayout import StackLayout
from kivy.core.image import Image
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition, WipeTransition, SwapTransition
import tweepy
   
#Twitter API credentials
consumer_key = "qsaZuBudT7HRaXf4JU0x0KtML"
consumer_secret = "C6hpOGEtzTc9xoCeABgEnWxwWXjp3qOIpxrNiYerCoSGXZRqEd"
access_key = "896619221475614720-MBUhORGyemI4ueSPdW8cAHJIaNzgdr9"
access_secret = "Lu47Nu4eQrtQI1vmKUIMWTQ419CmEXSZPVAyHb8vFJbTu"   
#authorize twitter, initialize tweepy
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_key, access_secret)
api = tweepy.API(auth)

errorlog = open('errorlog.txt','w')
mimiclog = open('mimiclog.txt','w')
locationlog = open('locationlog.txt','a')

iss_crew_url = 'http://www.howmanypeopleareinspacerightnow.com/peopleinspace.json'        
nasaissurl = 'http://spaceflight.nasa.gov/realdata/sightings/SSapplications/Post/JavaSSOP/orbit/ISS/SVPOST.html'
req = urllib2.Request("http://api.open-notify.org/iss-now.json")
TLE_req = urllib2.Request("http://spaceflight.nasa.gov/realdata/sightings/SSapplications/Post/JavaSSOP/orbit/ISS/SVPOST.html")

try:
    ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=0)
    print str(ser)
except:
    errorlog.write(str(datetime.datetime.utcnow()))
    errorlog.write(' ')
    errorlog.write("serial connection GPIO not found")
    errorlog.write('\n')

try:
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=0)
    print str(ser)
except:
    errorlog.write(str(datetime.datetime.utcnow()))
    errorlog.write(' ')
    errorlog.write("serial connection GPIO not found")
    errorlog.write('\n')

#try:
#    ser = serial.Serial('/dev/ttyAMA00', 115200, timeout=0)
#except:
#    print "No serial connection detected - AMA0"
#    errorlog.write(str(datetime.datetime.utcnow()))
#    errorlog.write(' ')
#    errorlog.write("serial connection GPIO not found")
#    errorlog.write('\n')

#ser = serial.Serial('/dev/ttyACM0', 115200, timeout=0)
#ser.write("test")

#try:
#    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=0)
#    ser.write("test")
    #ser.open()
#except:
#    print "No serial connection detected - USB"
#    errorlog.write(str(datetime.datetime.utcnow()))
#    errorlog.write(' ')
#    errorlog.write("serial connection USB not found")
#    errorlog.write('\n')
testfactor = -1
crew_mention= False
crewjsonsuccess = False
mimicbutton = False
fakeorbitboolean = False
zerocomplete = False
switchtofake = False
manualcontrol = False
startup = True
isscrew = 0
different_tweet = False
conn = sqlite3.connect('iss_telemetry.db') #sqlite database call change to include directory
c = conn.cursor() 
val = ""
testvalue = 0
alternate = True       
Beta4Bcontrol = False
Beta3Bcontrol = False
Beta2Bcontrol = False
Beta1Bcontrol = False
Beta4Acontrol = False
Beta3Acontrol = False
Beta2Acontrol = False
Beta1Acontrol = False
PSARJcontrol = False
SSARJcontrol = False
PTRRJcontrol = False
STRRJcontrol = False
stopAnimation = True
startingAnim = True
sizeX = 0.00
sizeY = 0.00
psarj2 = 1.0
ssarj2 = 1.0
new_x = 0
new_y = 0
new_x2 = 0
new_y2 = 0
psarj = 0.00
ssarj = 0.00
ptrrj = 0.00
strrj = 0.00
beta1b = 0.00
beta1a = 0.00
beta2b = 0.00
beta2a = 0.00
beta3b = 0.00
beta3a = 0.00
beta4b = 0.00
beta4a = 0.00
aos = 0.00
los = 0.00
seconds2 = 260
timenew = float(time.time())
timeold = 0.00
timenew2 = float(time.time())
timeold2 = 0.00
oldLOS = 0.00
psarjmc = 0.00
ssarjmc = 0.00
ptrrjmc = 0.00
strrjmc = 0.00
beta1bmc = 0.00
beta1amc = 0.00
beta2bmc = 0.00
beta2amc = 0.00
beta3bmc = 0.00
beta3amc = 0.00
beta4bmc = 0.00
beta4amc = 0.00
EVAinProgress = False
leak_hold = False
firstcrossing = True
position_x = 0.00
position_y = 0.00
position_z = 0.00
velocity_x = 0.00
velocity_y = 0.00
velocity_z = 0.00
velocity = 0.00
altitude = 0.00
mass = 0.00
c1b = 0.00
c1a = 0.00
c3b = 0.00
c3a = 0.00
airlock_pump = 0
crewlockpres = 758
EVA_activities = False
repress = False
depress = False
seconds = 0
minutes = 0
hours = 0
leak_hold = False
latest_tweet = "No Tweet"
crewmember = ['','','','','','','','','','','','']
crewmemberbio = ['','','','','','','','','','','','']
crewmembertitle = ['','','','','','','','','','','','']
crewmemberdays = ['','','','','','','','','','','','']
crewmemberpicture = ['','','','','','','','','','','','']
crewmembercountry = ['','','','','','','','','','','','']
EV1 = ""
EV2 = ""
numEVAs1 = ""
EVAtime_hours1 = ""
EVAtime_minutes1 = ""
numEVAs2 = ""
EVAtime_hours2 = ""
EVAtime_minutes2 = ""

EVA_picture_urls = []
urlindex = 0

def StringToBytes(val):
    retVal = []
    for c in val:
            retVal.append(ord(c))
    return retVal

class RotatedImage(Image):
    angle = NumericProperty()

class MainScreen(Screen):
    def changeManualControlBoolean(self, *args):
        global manualcontrol
        manualcontrol = args[0]        

class CalibrateScreen(Screen):
    def serialWrite(self, *args):
        ser.write(*args)
        #try:
        #    self.serialActualWrite(self, *args)
        #except:
        #    errorlog.write(str(datetime.datetime.utcnow()))
        #    errorlog.write(' ')
        #    errorlog.write("Attempted write - no serial device connected")
        #    errorlog.write('\n')

    def zeroJoints(self):
        self.changeBoolean(True)
        ser.write('Zero')

    def changeBoolean(self, *args):
        global zerocomplete
        zerocomplete = args[0]

class ManualControlScreen(Screen):
    def setActive(*args):
        global Beta4Bcontrol
        global Beta3Bcontrol
        global Beta2Bcontrol
        global Beta1Bcontrol
        global Beta4Acontrol
        global Beta3Acontrol
        global Beta2Acontrol
        global Beta1Acontrol
        global PSARJcontrol
        global SSARJcontrol
        global PTRRJcontrol
        global STRRJcontrol
	if str(args[1])=="Beta4B":
	    Beta4Bcontrol = True
	if str(args[1])=="Beta3B":
	    Beta3Bcontrol = True
	if str(args[1])=="Beta2B":
	    Beta2Bcontrol = True
	if str(args[1])=="Beta1B":
	    Beta1Bcontrol = True
	if str(args[1])=="Beta4A":
	    Beta4Acontrol = True
	if str(args[1])=="Beta3A":
	    Beta3Acontrol = True
	if str(args[1])=="Beta2A":
	    Beta2Acontrol = True
	if str(args[1])=="Beta1A":
	    Beta1Acontrol = True
	if str(args[1])=="PTRRJ":
	    PTRRJcontrol = True
	if str(args[1])=="STRRJ":
	    STRRJcontrol = True
	if str(args[1])=="PSARJ":
	    PSARJcontrol = True
	if str(args[1])=="SSARJ":
	    SSARJcontrol = True

    def incrementActive(self, *args):
        global Beta4Bcontrol
        global Beta3Bcontrol
        global Beta2Bcontrol
        global Beta1Bcontrol
        global Beta4Acontrol
        global Beta3Acontrol
        global Beta2Acontrol
        global Beta1Acontrol
        global PSARJcontrol
        global SSARJcontrol
        global PTRRJcontrol
        global STRRJcontrol

        if Beta4Bcontrol == True:
            self.incrementBeta4B(args[0])
        if Beta3Bcontrol == True:
            self.incrementBeta3B(args[0])
        if Beta2Bcontrol == True:
            self.incrementBeta2B(args[0])
        if Beta1Bcontrol == True:
            self.incrementBeta1B(args[0])
        if Beta4Acontrol == True:
            self.incrementBeta4A(args[0])
        if Beta3Acontrol == True:
            self.incrementBeta3A(args[0])
        if Beta2Acontrol == True:
            self.incrementBeta2A(args[0])
        if Beta1Acontrol == True:
            self.incrementBeta1A(args[0])
        if PTRRJcontrol == True:
            self.incrementPTRRJ(args[0])
        if STRRJcontrol == True:
            self.incrementSTRRJ(args[0])
        if PSARJcontrol == True:
            self.incrementPSARJ(args[0])
        if SSARJcontrol == True:
            self.incrementSSARJ(args[0])

    def incrementPSARJ(self, *args):
        global psarjmc
        psarjmc += args[1]
        self.serialWrite("PSARJ=" + str(psarjmc) + " ")   
     
    def incrementSSARJ(self, *args):
        global ssarjmc
        ssarjmc += args[1]
        self.serialWrite("SSARJ=" + str(ssarjmc) + " ")   
     
    def incrementPTTRJ(self, *args):
        global ptrrjmc
        ptrrjmc += args[1]
        self.serialWrite("PTRRJ=" + str(ptrrjmc) + " ")   
     
    def incrementSTRRJ(self, *args):
        global strrjmc
        strrjmc += args[1]
        self.serialWrite("STRRJ=" + str(strrjmc) + " ")   
     
    def incrementBeta1B(self, *args):
        global beta1bmc
        beta1bmc += args[1]
        self.serialWrite("Beta1B=" + str(beta1bmc) + " ")   
     
    def incrementBeta1A(self, *args):
        global beta1amc
        beta1amc += args[1]
        self.serialWrite("Beta1A=" + str(beta1amc) + " ")   
     
    def incrementBeta2B(self, *args):
        global beta2bmc
        beta2bmc += args[1]
        self.serialWrite("Beta2B=" + str(beta2bmc) + " ")   
     
    def incrementBeta2A(self, *args):
        global beta2amc
        beta2amc += args[1]
        self.serialWrite("Beta2A=" + str(beta2amc) + " ")   
     
    def incrementBeta3B(self, *args):
        global beta3bmc
        beta3bmc += args[1]
        self.serialWrite("Beta3B=" + str(beta3bmc) + " ")   
     
    def incrementBeta3A(self, *args):
        global beta3amc
        beta3amc += args[1]
        self.serialWrite("Beta3A=" + str(beta3amc) + " ")   
     
    def incrementBeta4B(self, *args):
        global beta4bmc
        beta4bmc += args[1]
        self.serialWrite("Beta4B=" + str(beta4bmc) + " ")   
     
    def incrementBeta4A(self, *args):
        global beta4amc
        beta4amc += args[1]
        self.serialWrite("Beta4A=" + str(beta4amc) + " ")   
     
    def changeBoolean(self, *args):
        global manualcontrol
        manualcontrol = args[0]
    
    def serialWrite(self, *args):
        print args
        ser.write(*args)

class FakeOrbitScreen(Screen):
    def serialWrite(self, *args):
        ser.write(*args)

    def changeBoolean(self, *args):
        global fakeorbitboolean
        global switchtofake
        switchtofake = args[0]
        fakeorbitboolean = args[0]

class Settings_Screen(Screen, EventDispatcher):
    pass

class Orbit_Screen(Screen, EventDispatcher):
    pass

class EPS_Screen(Screen, EventDispatcher):
    pass

class CT_Screen(Screen, EventDispatcher):
    pass

class EVA_Screen(Screen, EventDispatcher):
    pass

class EVA_Pictures(Screen, EventDispatcher):
    pass

class TCS_Screen(Screen, EventDispatcher):
    pass

class Crew_Screen(Screen, EventDispatcher):
    pass

class MimicScreen(Screen, EventDispatcher):
    def changeMimicBoolean(self, *args):
        global mimicbutton
        mimicbutton = args[0]
    
    def changeSwitchBoolean(self, *args):
        global switchtofake
        switchtofake = args[0]

class MainScreenManager(ScreenManager):
    pass

class MyButton(Button):
    pass

class MainApp(App):

    def build(self):
        global startup
        global crewjsonsuccess
        global stopAnimation
        global event_fadeISS
        self.main_screen = MainScreen(name = 'main')
        #root.add_widget(MainScreen(name = 'main'))
        self.orbit_screen = Orbit_Screen(name = 'orbit')
        self.fakeorbit_screen = FakeOrbitScreen(name = 'fakeorbit')
        self.mimic_screen = MimicScreen(name = 'mimic')
        self.eps_screen = EPS_Screen(name = 'eps')
        self.ct_screen = CT_Screen(name = 'ct')
        self.tcs_screen = TCS_Screen(name = 'tcs')
        self.crew_screen = Crew_Screen(name = 'crew')
        self.settings_screen = Settings_Screen(name = 'settings')
        self.eva_screen = EVA_Screen(name='eva')
        self.eva_pictures = EVA_Pictures(name='eva_pictures')

        root = MainScreenManager(transition=WipeTransition())
        #root.add_widget(MainScreen(name = 'main'))
        root.add_widget(CalibrateScreen(name = 'calibrate'))
        root.add_widget(self.mimic_screen)
        root.add_widget(self.main_screen)
        root.add_widget(self.fakeorbit_screen)
        root.add_widget(self.orbit_screen)
        root.add_widget(self.eps_screen)
        root.add_widget(self.ct_screen)
        root.add_widget(self.eva_screen)
        root.add_widget(self.eva_pictures)
        root.add_widget(self.tcs_screen)
        root.add_widget(self.crew_screen)
        root.add_widget(self.settings_screen)
        root.add_widget(ManualControlScreen(name = 'manualcontrol'))
        root.current = 'eva' #change this back to main when done with eva setup

        Clock.schedule_interval(self.update_labels, 1)
        Clock.schedule_interval(self.deleteURLPictures, 86400)
        Clock.schedule_interval(self.animate3,0.1)
        Clock.schedule_interval(self.checkAOSlong, 5)
        Clock.schedule_interval(self.checkCrew, 3600)
        Clock.schedule_interval(self.checkTwitter, 65) #change back to 65 after testing
        Clock.schedule_interval(self.changePictures, 10)
        if crewjsonsuccess == False: #check crew every 10s until success then once per hour
            Clock.schedule_once(self.checkCrew, 10)
        if startup == True:
            startup = False
            #self.checkCrew(60)

        #Clock.schedule_interval(self.getTLE, 3600)
        return root

    def deleteURLPictures(self, dt):
        mimiclog.write(str(datetime.datetime.utcnow()))
        mimiclog.write(' ')
        mimiclog.write(str("deleteURLpictures"))
        mimiclog.write('\n')
        global EVA_picture_urls
        del EVA_picture_urls[:]
        EVA_picture_urls[:] = []

    def changePictures(self, dt):
        mimiclog.write(str(datetime.datetime.utcnow()))
        mimiclog.write(' ')
        mimiclog.write(str("changeURLpictures"))
        mimiclog.write('\n')
        global EVA_picture_urls
        global urlindex
        urlsize = len(EVA_picture_urls)
        
        if urlsize > 0:
            self.eva_screen.ids.EVAimage.source = EVA_picture_urls[urlindex]
            self.eva_pictures.ids.EVAimage.source = EVA_picture_urls[urlindex]
        
        urlindex = urlindex + 1
        if urlindex > urlsize-1:
            urlindex = 0

    def check_EVA_stats(self,lastname1,firstname1,lastname2,firstname2):                
        mimiclog.write(str(datetime.datetime.utcnow()))
        mimiclog.write(' ')
        mimiclog.write(str("check EVA stats"))
        mimiclog.write('\n')

        global numEVAs1
        global EVAtime_hours1
        global EVAtime_minutes1
        global numEVAs2
        global EVAtime_hours2
        global EVAtime_minutes2
        global EV1
        global EV2

        eva_url = 'http://spacefacts.de/eva/e_eva_az.htm'
        urlthingy = urllib2.urlopen(eva_url)
        soup = BeautifulSoup(urlthingy, 'html.parser')
        
        numEVAs1 = 0
        EVAtime_hours1 = 0
        EVAtime_minutes1 = 0
        numEVAs2 = 0
        EVAtime_hours2 = 0
        EVAtime_minutes2 = 0

        tabletags = soup.find_all("td")
        for tag in tabletags:
            if lastname1 in tag.text:
                if firstname1 in tag.find_next_sibling("td").text:
                    numEVAs1 = tag.find_next_sibling("td").find_next_sibling("td").find_next_sibling("td").text
                    EVAtime_hours1 = int(tag.find_next_sibling("td").find_next_sibling("td").find_next_sibling("td").find_next_sibling("td").text)
                    EVAtime_minutes1 = int(tag.find_next_sibling("td").find_next_sibling("td").find_next_sibling("td").find_next_sibling("td").find_next_sibling("td").text)
                    EVAtime_minutes1 += (EVAtime_hours1 * 60)

        for tag in tabletags:
            if lastname2 in tag.text:
                if firstname2 in tag.find_next_sibling("td").text:
                    numEVAs2 = tag.find_next_sibling("td").find_next_sibling("td").find_next_sibling("td").text
                    EVAtime_hours2 = int(tag.find_next_sibling("td").find_next_sibling("td").find_next_sibling("td").find_next_sibling("td").text)
                    EVAtime_minutes2 = int(tag.find_next_sibling("td").find_next_sibling("td").find_next_sibling("td").find_next_sibling("td").find_next_sibling("td").text)
                    EVAtime_minutes2 += (EVAtime_hours2 * 60)
        
        EV1_EVA_number = numEVAs1 
        EV1_EVA_time  = EVAtime_minutes1
        EV2_EVA_number = numEVAs2 
        EV2_EVA_time  = EVAtime_minutes2

        EV1_minutes = str(EV1_EVA_time%60).zfill(2)
        EV2_minutes = str(EV2_EVA_time%60).zfill(2)
        EV1_hours = int(EV1_EVA_time/60)
        EV2_hours = int(EV2_EVA_time/60)

        self.eva_screen.ids.EV1.text = str(EV1) + " (EV1):"
        self.eva_screen.ids.EV2.text = str(EV2) + " (EV2):"
        self.eva_screen.ids.EV1_EVAnum.text = "Number of EVAs = " + str(EV1_EVA_number) 
        self.eva_screen.ids.EV2_EVAnum.text = "Number of EVAs = " + str(EV2_EVA_number)
        self.eva_screen.ids.EV1_EVAtime.text = "Total EVA Time = " + str(EV1_hours) + "h " + str(EV1_minutes) + "m"
        self.eva_screen.ids.EV2_EVAtime.text = "Total EVA Time = " + str(EV2_hours) + "h " + str(EV2_minutes) + "m"

    def checkTwitter(self, dt):
        background_thread = Thread(target=self.checkTwitter2)
        background_thread.daemon = True
        background_thread.start()


    def checkTwitter2(self):
        mimiclog.write(str(datetime.datetime.utcnow()))
        mimiclog.write(' ')
        mimiclog.write(str("check twitter"))
        mimiclog.write('\n')
        
        global latest_tweet
        global crew_mention
        global different_tweet
        global crewmember
        global crewmemberpicture
        global numEVAs1
        global EVAtime_hours1
        global EVAtime_minutes1
        global numEVAs2
        global EVAtime_hours2
        global EVAtime_minutes2
        global EV1
        global EV2

        try:
            #stuff = api.user_timeline(screen_name = 'iss101', count = 1, include_rts = True, tweet_mode = 'extended')
            stuff = api.user_timeline(screen_name = 'iss_mimic', count = 1, include_rts = True, tweet_mode = 'extended')
        except:
            errorlog.write(str(datetime.datetime.utcnow()))
            errorlog.write(' ')
            errorlog.write("Tweepy - Error Retrieving Tweet, make sure clock is correct")
            errorlog.write('\n')
        try:
            stuff
        except NameError:
            print "No tweet - ensure correct time is set"
        else:
            for status in stuff:
                if status.full_text == latest_tweet:
                    different_tweet = False
                else:
                    different_tweet = True

                latest_tweet = status.full_text
                if u'extended_entities' in status._json:
                    if u'media' in status._json[u'extended_entities']:
                        for pic in status._json[u'extended_entities'][u'media']:
                            EVA_picture_urls.append(str(pic[u'media_url']))

        emoji_pattern = re.compile("["u"\U0000007F-\U0001F1FF""]+", flags=re.UNICODE)
        tweet_string_no_emojis = str(emoji_pattern.sub(r'?', latest_tweet)) #cleanse the emojis!!
        self.eva_screen.ids.EVAstatus.text = str(tweet_string_no_emojis.split("http",1)[0])

        EVnames = []
        EVpics = []
        index = 0

        if ("EVA BEGINS" in latest_tweet) and latest_tweet.count('@') == 2 and different_tweet:
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
                EVpics[count] = EVpics[count].replace("_normal","_bigger")
                count += 1

        if crew_mention:
            EV1_surname = EVnames[0].split()[-1]
            EV1_firstname = EVnames[0].split()[0]
            #EV1_surname = 'Bresnik'
            EV2_surname = EVnames[1].split()[-1]
            EV2_firstname = EVnames[1].split()[0]
            #EV2_surname = 'Hei'
            EV1 = EVnames[0]
            EV2 = EVnames[1]
            self.eva_screen.ids.EV1_Pic.source = str(EVpics[0])
            self.eva_screen.ids.EV2_Pic.source = str(EVpics[1])

            background_thread = Thread(target=self.check_EVA_stats, args=(EV1_surname,EV1_firstname,EV2_surname,EV2_firstname))
            background_thread.daemon = True
            background_thread.start()
            #self.check_EVA_stats(EV1_surname,EV2surname)
            
            crew_mention = False
            
    def flashEVAbutton(self, instace):
        mimiclog.write(str(datetime.datetime.utcnow()))
        mimiclog.write(' ')
        mimiclog.write(str("flash eva button"))
        mimiclog.write('\n')
        global EVAinProgress

        self.mimic_screen.ids.EVA_button.background_color = (0,0,1,1)
        def reset_color(*args):
            self.mimic_screen.ids.EVA_button.background_color = (1,1,1,1)
        Clock.schedule_once(reset_color, 0.5) 
    
    def EVA_clock(self, dt):
        mimiclog.write(str(datetime.datetime.utcnow()))
        mimiclog.write(' ')
        mimiclog.write(str("eva timer"))
        mimiclog.write('\n')
        global seconds
        global minutes
        global hours
        global timenew
        global timeold
                          
        timenew = float(time.time())
        difference = timenew - timeold
        if difference > 1000: #first call to this function will have large time difference
            difference = 0
        timeold = timenew

        seconds += difference
        if seconds >= 60:
            seconds = 0
            minutes += 1
            if minutes >= 60:
                minutes = 0
                hours += 1
        self.eva_screen.ids.EVA_clock.text =(str(hours) + ":" + str(minutes).zfill(2) + ":" + str(int(seconds)).zfill(2))
        self.eva_screen.ids.EVA_clock.color = 0.33,0.7,0.18

    def animate(self, instance):
        mimiclog.write(str(datetime.datetime.utcnow()))
        mimiclog.write(' ')
        mimiclog.write(str("animate"))
        mimiclog.write('\n')
        global new_x2
        global new_y2
        self.main_screen.ids.ISStiny2.size_hint = 0.07,0.07
        new_x2 = new_x2+0.007
        new_y2 = (math.sin(new_x2*30)/18)+0.75
        if new_x2 > 1:
            new_x2 = new_x2-1.0
        self.main_screen.ids.ISStiny2.pos_hint = {"center_x": new_x2, "center_y": new_y2}

    def animate3(self, instance):
        mimiclog.write(str(datetime.datetime.utcnow()))
        mimiclog.write(' ')
        mimiclog.write(str("animate3"))
        mimiclog.write('\n')
        global new_x
        global new_y
        global sizeX
        global sizeY
        global startingAnim
        if new_x<0.886:
            new_x = new_x+0.007
            new_y = (math.sin(new_x*30)/18)+0.75
            self.main_screen.ids.ISStiny.pos_hint = {"center_x": new_x, "center_y": new_y}
        else:
            if sizeX <= 0.15:
                sizeX = sizeX + 0.01
                sizeY = sizeY + 0.01
                self.main_screen.ids.ISStiny.size_hint = sizeX,sizeY
            else:
                if startingAnim:
                    Clock.schedule_interval(self.animate,0.1)
                    startingAnim = False

    def serialWrite(self, *args):
        ser.write(*args)
        #try:
        #   ser.write(*args)
        #except:
        #   errorlog.write(str(datetime.datetime.utcnow()))
        #   errorlog.write(' ')
        #   errorlog.write("Attempted write - no serial device connected")
        #   errorlog.write('\n')

    def changeColors(self, *args):   #this function sets all labels on mimic screen to a certain color based on signal status
        self.eps_screen.ids.psarj_value.color = args[0],args[1],args[2]
        self.eps_screen.ids.ssarj_value.color = args[0],args[1],args[2]
        self.tcs_screen.ids.ptrrj_value.color = args[0],args[1],args[2]
        self.tcs_screen.ids.strrj_value.color = args[0],args[1],args[2]
        self.eps_screen.ids.beta1a_value.color = args[0],args[1],args[2]
        self.eps_screen.ids.beta1b_value.color = args[0],args[1],args[2]
        self.eps_screen.ids.beta2a_value.color = args[0],args[1],args[2]
        self.eps_screen.ids.beta2b_value.color = args[0],args[1],args[2]
        self.eps_screen.ids.beta3a_value.color = args[0],args[1],args[2]
        self.eps_screen.ids.beta3b_value.color = args[0],args[1],args[2]
        self.eps_screen.ids.beta4a_value.color = args[0],args[1],args[2]
        self.eps_screen.ids.beta4b_value.color = args[0],args[1],args[2]
        
        self.eps_screen.ids.c1a_value.color = args[0],args[1],args[2]
        self.eps_screen.ids.v1a_value.color = args[0],args[1],args[2]
        self.eps_screen.ids.c1b_value.color = args[0],args[1],args[2]
        self.eps_screen.ids.v1b_value.color = args[0],args[1],args[2]
        self.eps_screen.ids.c2a_value.color = args[0],args[1],args[2]
        self.eps_screen.ids.v2a_value.color = args[0],args[1],args[2]
        self.eps_screen.ids.c2b_value.color = args[0],args[1],args[2]
        self.eps_screen.ids.v2b_value.color = args[0],args[1],args[2]
        self.eps_screen.ids.c3a_value.color = args[0],args[1],args[2]
        self.eps_screen.ids.v3a_value.color = args[0],args[1],args[2]
        self.eps_screen.ids.c3b_value.color = args[0],args[1],args[2]
        self.eps_screen.ids.v3b_value.color = args[0],args[1],args[2]
        self.eps_screen.ids.c4a_value.color = args[0],args[1],args[2]
        self.eps_screen.ids.v4a_value.color = args[0],args[1],args[2]
        self.eps_screen.ids.c4b_value.color = args[0],args[1],args[2]
        self.eps_screen.ids.v4b_value.color = args[0],args[1],args[2]
        
        self.mimic_screen.ids.aosvalue.color = args[0],args[1],args[2]
    
    def changeManualControlBoolean(self, *args):
        global manualcontrol
        manualcontrol = args[0]
        
    #this code based on code from natronics open-notify.org
    def getTLE(self, *args):
        try:
            self.fetchTLE(self, *args)
        except:
            errorlog.write(str(datetime.datetime.utcnow()))
            errorlog.write(' ')
            errorlog.write("TLE Fetch - URL Error")
            errorlog.write('\n')
            print "TLE Fetch - URL Error"

    def fetchTLE(self, *args):
        TLE = BeautifulSoup(urllib2.urlopen(nasaissurl), 'html.parser')
        WebpageStuff = TLE.find('pre') 
        TLE_reduced = WebpageStuff.split('TWO LINE MEAN ELEMENT SET')
        print TLE_reduced
        #TLE_response = urllib2.urlopen(TLE_req)
        #TLE_read = TLE_response.read()
        #TLE_read = TLE_read.split("<PRE>")[1]
        #TLE_read = TLE_read.split("</PRE>")[0]
        #TLE_read = TLE_read.split("Vector Time (GMT): ")[1:]
        
         #print TLE_read
         #print group
        
         #for group in TLE_read:
         #   tle = group.split("TWO LINE MEAN ELEMENT SET")[1]
         #   tle = tle[8:160]
         #   lines = tle.split('\n')[0:3]
         #   print lines
        
    def updateCrew(self, dt):
        try:
            self.checkCrew(self, *args)
        except:
            errorlog.write(str(datetime.datetime.utcnow()))
            errorlog.write(' ')
            errorlog.write("Crew Check - URL Error")
            errorlog.write('\n')
            print "Crew Check URL Error"
    
    def checkCrew(self, dt):
        #crew_response = urllib2.urlopen(crew_req)
        global isscrew    
        global crewmember 
        global crewmemberbio
        global crewmembertitle
        global crewmemberdays
        global crewmemberpicture
        global crewmembercountry
        req = urllib2.Request(iss_crew_url, headers={'User-Agent' : "Magic Browser"})
        global ser
        stuff = urllib2.urlopen(req)
        now = datetime.datetime.now()
        if (stuff.info().getsubtype()=='json'):
            mimiclog.write(str(datetime.datetime.utcnow()))
            mimiclog.write(' ')
            mimiclog.write("Crew Check - JSON Success")
            mimiclog.write('\n')
            crewjsonsuccess = True
            data = json.load(stuff)
            number_of_space = int(data['number'])
            for num in range(1,number_of_space+1):
                if(str(data['people'][num-1]['location']) == str("International Space Station")):
                    crewmember[isscrew] = str(data['people'][num-1]['name'])
                    crewmemberbio[isscrew] = (data['people'][num-1]['bio'])
                    crewmembertitle[isscrew] = str(data['people'][num-1]['title'])
                    datetime_object = datetime.datetime.strptime(str(data['people'][num-1]['launchdate']),'%Y-%m-%d')
                    previousdays = int(data['people'][num-1]['careerdays'])
                    totaldaysinspace = str(now-datetime_object)
                    d_index = totaldaysinspace.index('d')
                    crewmemberdays[isscrew] = str(int(totaldaysinspace[:d_index])+previousdays)+" days in space"
                    crewmemberpicture[isscrew] = str(data['people'][num-1]['biophoto'])
                    crewmembercountry[isscrew] = str(data['people'][num-1]['country']).title()
                    if(str(data['people'][num-1]['country'])==str('usa')):
                        crewmembercountry[isscrew] = str('USA')
                    isscrew = isscrew+1  
        else:
            mimiclog.write(str(datetime.datetime.utcnow()))
            mimiclog.write(' ')
            mimiclog.write("Crew Check - JSON Error")
            mimiclog.write('\n')
            crewjsonsuccess = False

        #print crewmemberpicture[0]
        isscrew = 0
        self.crew_screen.ids.crew1.text = crewmember[0]  
        self.crew_screen.ids.crew1title.text = crewmembertitle[0]  
        self.crew_screen.ids.crew1country.text = crewmembercountry[0]  
        self.crew_screen.ids.crew1daysonISS.text = crewmemberdays[0]
        #self.crew_screen.ids.crew1image.source = str(crewmemberpicture[0])
        self.crew_screen.ids.crew2.text = crewmember[1]  
        self.crew_screen.ids.crew2title.text = crewmembertitle[1]  
        self.crew_screen.ids.crew2country.text = crewmembercountry[1]  
        self.crew_screen.ids.crew2daysonISS.text = crewmemberdays[1]
        #self.crew_screen.ids.crew2image.source = str(crewmemberpicture[1])
        self.crew_screen.ids.crew3.text = crewmember[2]  
        self.crew_screen.ids.crew3title.text = crewmembertitle[2]  
        self.crew_screen.ids.crew3country.text = crewmembercountry[2]  
        self.crew_screen.ids.crew3daysonISS.text = crewmemberdays[2]
        #self.crew_screen.ids.crew3image.source = str(crewmemberpicture[2])
        self.crew_screen.ids.crew4.text = crewmember[3]  
        self.crew_screen.ids.crew4title.text = crewmembertitle[3]  
        self.crew_screen.ids.crew4country.text = crewmembercountry[3]  
        self.crew_screen.ids.crew4daysonISS.text = crewmemberdays[3]
        #self.crew_screen.ids.crew4image.source = str(crewmemberpicture[3])
        self.crew_screen.ids.crew5.text = crewmember[4]  
        self.crew_screen.ids.crew5title.text = crewmembertitle[4]  
        self.crew_screen.ids.crew5country.text = crewmembercountry[4]  
        self.crew_screen.ids.crew5daysonISS.text = crewmemberdays[4]
        #self.crew_screen.ids.crew5image.source = str(crewmemberpicture[4])
        self.crew_screen.ids.crew6.text = crewmember[5]  
        self.crew_screen.ids.crew6title.text = crewmembertitle[5]  
        self.crew_screen.ids.crew6country.text = crewmembercountry[5]  
        self.crew_screen.ids.crew6daysonISS.text = crewmemberdays[5]
        #self.crew_screen.ids.crew6image.source = str(crewmemberpicture[5])
        self.crew_screen.ids.crew7.text = crewmember[6]  
        self.crew_screen.ids.crew7title.text = crewmembertitle[6]  
        self.crew_screen.ids.crew7country.text = crewmembercountry[6]  
        self.crew_screen.ids.crew7daysonISS.text = crewmemberdays[6]
        #self.crew_screen.ids.crew7image.source = str(crewmemberpicture[6])
        self.crew_screen.ids.crew8.text = crewmember[7]  
        self.crew_screen.ids.crew8title.text = crewmembertitle[7]  
        self.crew_screen.ids.crew8country.text = crewmembercountry[7]  
        self.crew_screen.ids.crew8daysonISS.text = crewmemberdays[7]
        #self.crew_screen.ids.crew8image.source = str(crewmemberpicture[7])
        self.crew_screen.ids.crew9.text = crewmember[8]  
        self.crew_screen.ids.crew9title.text = crewmembertitle[8]  
        self.crew_screen.ids.crew9country.text = crewmembercountry[8]  
        self.crew_screen.ids.crew9daysonISS.text = crewmemberdays[8]
        #self.crew_screen.ids.crew9image.source = str(crewmemberpicture[8])
        self.crew_screen.ids.crew10.text = crewmember[9]  
        self.crew_screen.ids.crew10title.text = crewmembertitle[9]  
        self.crew_screen.ids.crew10country.text = crewmembercountry[9]  
        self.crew_screen.ids.crew10daysonISS.text = crewmemberdays[9]
        #self.crew_screen.ids.crew10image.source = str(crewmemberpicture[9])
        self.crew_screen.ids.crew11.text = crewmember[10]  
        self.crew_screen.ids.crew11title.text = crewmembertitle[10]  
        self.crew_screen.ids.crew11country.text = crewmembercountry[10]  
        self.crew_screen.ids.crew11daysonISS.text = crewmemberdays[10]
        #self.crew_screen.ids.crew11image.source = str(crewmemberpicture[10])
        self.crew_screen.ids.crew12.text = crewmember[11]  
        self.crew_screen.ids.crew12title.text = crewmembertitle[11]  
        self.crew_screen.ids.crew12country.text = crewmembercountry[11]  
        self.crew_screen.ids.crew12daysonISS.text = crewmemberdays[11]
        #self.crew_screen.ids.crew12image.source = str(crewmemberpicture[11]) 
        
    def checkAOSlong(self, dt):
        global aos
        #if float(aos) == 0.00: #getting url errors, killing for now
            #print "signal lost - writing longitude"
            #response = urllib2.urlopen(req)
            #obj = json.loads(response.read())
            #locationlog.write("time ")
            #locationlog.write(str(obj['timestamp']))
            #locationlog.write(" long ")
            #locationlog.write(str(obj['iss_position']['longitude']))
            #locationlog.write('\n')
    def map_rotation(self, args):
        scalefactor = 0.083333
        scaledValue = float(args)/scalefactor
        return scaledValue

    def map_psi_bar(self, args):
        scalefactor = 0.014666666667
        scaledValue = (float(args)*scalefactor)+0.71
        return scaledValue
    
    def map_hold_bar(self, args):
        scalefactor = 0.000923
        scaledValue = (float(args)*scalefactor)+0.7
        return scaledValue
    
    def hold_timer(self, dt):
        mimiclog.write(str(datetime.datetime.utcnow()))
        mimiclog.write(' ')
        mimiclog.write(str("hold timer"))
        mimiclog.write('\n')
        global seconds2
        global timenew2
        global timeold2
                          
        timenew2 = float(time.time())
        difference2 = timenew2 - timeold2
        if difference2 > 1000: #first call to this function will have large time difference
            difference2 = 0
        timeold2 = timenew2
        seconds2 -= difference2
        new_bar_x = self.map_hold_bar(260-seconds2)
        self.eva_screen.ids.leak_timer.text = "~"+ str(int(seconds2)) + "s"
        self.eva_screen.ids.Hold_bar.pos_hint = {"center_x": new_bar_x, "center_y": 0.484}
        self.eva_screen.ids.Crewlock_Status_image.source = './imgs/eva/LeakCheckLights.png'
        
        if seconds2 <= 0:
            seconds2 = 0
            Clock.unschedule(self.hold_timer)
            self.eva_screen.ids.leak_timer.text = "Complete"
            self.eva_screen.ids.Crewlock_Status_image.source = './imgs/eva/DepressLights.png'

    def update_labels(self, dt):
        global mimicbutton,switchtofake,fakeorbitboolean,psarj2,ssarj2,manualcontrol,psarj,ssarj,ptrrj,strrj,beta1b,beta1a,beta2b,beta2a,beta3b,beta3a,beta4b,beta4a,aos,los,oldLOS,psarjmc,ssarjmc,ptrrjmc,strrjmc,beta1bmc,beta1amc,beta2bmc,beta2amc,beta3bmc,beta3amc,beta4bmc,beta4amc,EVAinProgress,position_x,position_y,position_z,velocity_x,velocity_y,velocity_z,altitude,velocity,iss_mass,c1a,c1b,c3a,c3b,testvalue,testfactor,airlock_pump,crewlockpres,leak_hold,firstcrossing,EVA_activities,repress,depress
        
        c.execute('select Value from telemetry')
        values = c.fetchall()
        c.execute('select Timestamp from telemetry')
        timestamps = c.fetchall()
        
        psarj = "{:.2f}".format(float((values[0])[0]))
        if switchtofake == False:
            psarj2 = float(psarj)
        if manualcontrol == False:
            psarjmc = float(psarj)
        ssarj = "{:.2f}".format(float((values[1])[0]))
        if switchtofake == False:
            ssarj2 = float(ssarj)
        if manualcontrol == False:
            ssarjmc = float(ssarj)
        ptrrj = "{:.2f}".format(float((values[2])[0]))
        if manualcontrol == False:
            ptrrjmc = float(ptrrj)
        strrj = "{:.2f}".format(float((values[3])[0]))
        if manualcontrol == False:
            strrjmc = float(strrj)
        beta1b = "{:.2f}".format(float((values[4])[0]))
        if manualcontrol == False:
            beta1bmc = float(beta1b)
        beta1a = "{:.2f}".format(float((values[5])[0]))
        if manualcontrol == False:
            beta1amc = float(beta1a)
        beta2b = "{:.2f}".format(float((values[6])[0]))
        if manualcontrol == False:
            beta2bmc = float(beta2b)
        beta2a = "{:.2f}".format(float((values[7])[0]))
        if manualcontrol == False:
            beta2amc = float(beta2a)
        beta3b = "{:.2f}".format(float((values[8])[0]))
        if manualcontrol == False:
            beta3bmc = float(beta3b)
        beta3a = "{:.2f}".format(float((values[9])[0]))
        if manualcontrol == False:
            beta3amc = float(beta3a)
        beta4b = "{:.2f}".format(float((values[10])[0]))
        if manualcontrol == False:
            beta4bmc = float(beta4b)
        beta4a = "{:.2f}".format(float((values[11])[0]))
        if manualcontrol == False:
            beta4amc = float(beta4a)
        aos = "{:.2f}".format(int((values[12])[0]))
        los = "{:.2f}".format(int((values[13])[0]))      
        sasa_el = "{:.2f}".format(float((values[14])[0]))
        sgant_el = "{:.2f}".format(float((values[15])[0]))
        difference = float(sgant_el)-float(sasa_el) 
        v1a = "{:.2f}".format(float((values[25])[0]))
        v1b = "{:.2f}".format(float((values[26])[0]))
        v2a = "{:.2f}".format(float((values[27])[0]))
        v2b = "{:.2f}".format(float((values[28])[0]))
        v3a = "{:.2f}".format(float((values[29])[0]))
        v3b = "{:.2f}".format(float((values[30])[0]))
        v4a = "{:.2f}".format(float((values[31])[0]))
        v4b = "{:.2f}".format(float((values[32])[0]))
        c1a = "{:.2f}".format(float((values[33])[0]))
        c1b = "{:.2f}".format(float((values[34])[0]))
        c2a = "{:.2f}".format(float((values[35])[0]))
        c2b = "{:.2f}".format(float((values[36])[0]))
        c3a = "{:.2f}".format(float((values[37])[0]))
        c3b = "{:.2f}".format(float((values[38])[0]))
        c4a = "{:.2f}".format(float((values[39])[0]))
        c4b = "{:.2f}".format(float((values[40])[0]))
        
        airlock_pump = int((values[71])[0])
        crewlockpres = float((values[16])[0])
        #reverse = False 
        #if(crewlockpres <= 2):
        #    airlock_pump = 0
        #    reverse = True

        #if reverse:
        #    airlock_pump = 0
        #    testfactor = 1
        #else:
        #    airlock_pump = 1

        #if(float(crewlockpres) >= 758):
        #    airlock_pump = 1
        #    reverse = False

        #if testfactor == 1:
        #    airlock_pump = 0
        #else:
        #    airlock_pump = 1

        #crewlockpres = crewlockpres - (-10*testfactor)

        if airlock_pump==1 or crewlockpres < 744:
            EVA_activities = True
            Clock.schedule_interval(self.flashEVAbutton, 1)
            self.eva_screen.ids.EVA_occuring.color = 0,0,1
            self.eva_screen.ids.EVA_occuring.text = "EVA Standby"

        if airlock_pump==0 and crewlockpres > 744:
            EVA_activities = False
            self.eva_screen.ids.EVA_occuring.text = "Currently No EVA"
            self.eva_screen.ids.EVA_occuring.color = 1,0,0
            Clock.unschedule(self.flashEVAbutton)

        if 0.0193368*crewlockpres < 0.0386735: #PSI
            EVAinProgress = True
            self.eva_screen.ids.EVA_occuring.text = "EVA In Progress!!!"
            self.eva_screen.ids.EVA_occuring.color = 0.33,0.7,0.18
            self.eva_screen.ids.leak_timer.text = "Complete"
            self.eva_screen.ids.Crewlock_Status_image.source = './imgs/eva/InProgressLights.png'
            Clock.schedule_interval(self.EVA_clock, 1)

        if crewlockpres > 744 and ~airlock_pump:
            self.eva_screen.ids.leak_timer.text = ""


        if 0.0193368*crewlockpres > 0.0386735 and EVAinProgress: #PSI
            EVAinProgress = False
            Clock.unschedule(self.EVA_clock)
        
        if crewlockpres >= 744: #torr
            EVAinProgress = False
            self.eva_screen.ids.Crewlock_Status_image.source = './imgs/eva/BlankLights.png'
            
        if crewlockpres >= 700: #Torr
            leak_hold = False
            firstcrossing = True
        
        if crewlockpres <= 258.5 and firstcrossing and airlock_pump: #Torr
            leak_hold = True
            firstcrossing = False
            self.eva_screen.ids.EVA_occuring.text = "Leak Check in Progress!"
            self.eva_screen.ids.EVA_occuring.color = 0,0,1
            Clock.schedule_interval(self.hold_timer, 1)

        if leak_hold and crewlockpres < 256 and ~repress and airlock_pump:
            self.eva_screen.ids.EVA_occuring.text = "Crewlock Depressurizing"
            self.eva_screen.ids.EVA_occuring.color = 0,0,1
            leak_hold = False
            Clock.unschedule(self.hold_timer)
            self.eva_screen.ids.Hold_bar.pos_hint = {"center_x": 0.94, "center_y": 0.484}
            self.eva_screen.ids.leak_timer.text = "Complete"
            self.eva_screen.ids.Crewlock_Status_image.source = './imgs/eva/DepressLights.png'

        if airlock_pump == 1 and ~leak_hold and crewlockpres < 744:
            self.eva_screen.ids.EVA_occuring.text = "Crewlock Depressurizing"
            self.eva_screen.ids.EVA_occuring.color = 0,0,1
            #iself.eva_screen.ids.leak_timer.text = "Leak Check Timer"
            depress = True
            repress = False
            self.eva_screen.ids.Crewlock_Status_image.source = './imgs/eva/DepressLights.png'
        
        if airlock_pump == 0 and crewlockpres > 5 and crewlockpres < 744:
            self.eva_screen.ids.EVA_occuring.text = "Crewlock Repressurizing"
            self.eva_screen.ids.EVA_occuring.color = 0,0,1
            repress = True
            depress = False
            self.eva_screen.ids.Crewlock_Status_image.source = './imgs/eva/RepressLights.png'

#        if (difference > -10) && (isinstance(App.get_running_app().root_window.children[0], Popup)==False):
#            LOSpopup = Popup(title='Loss of Signal', content=Label(text='Possible LOS Soon'),size_hint=(0.3,0.2),auto_dismiss=True)
#            LOSpopup.open()
#            print "popup"    

        iss_mass = "{:.2f}".format(float((values[48])[0]))
        position_x = "{:.2f}".format(float((values[55])[0]))
        position_y = "{:.2f}".format(float((values[56])[0]))
        position_z = "{:.2f}".format(float((values[57])[0]))
        velocity_x = "{:.2f}".format(float((values[58])[0]))
        velocity_y = "{:.2f}".format(float((values[59])[0]))
        velocity_z = "{:.2f}".format(float((values[60])[0]))
        
        altitude = "{:.2f}".format((math.sqrt( math.pow(float(position_x), 2) + math.pow(float(position_y), 2) + math.pow(float(position_z), 2) )-6371.00))
        velocity = "{:.2f}".format(((math.sqrt( math.pow(float(velocity_x), 2) + math.pow(float(velocity_y), 2) + math.pow(float(velocity_z), 2) ))/1.00))

        if (fakeorbitboolean == True and (mimicbutton == True or switchtofake == True)):
            if psarj2 <= 0.00:
                psarj2 = 360.0
            self.fakeorbit_screen.ids.fakepsarj_value.text = "{:.2f}".format(psarj2)
            if ssarj2 >= 360.00:                
                ssarj2 = 0.0
            self.fakeorbit_screen.ids.fakessarj_value.text = "{:.2f}".format(ssarj2)
            
            psarj2 -= 0.0666
            ssarj2 += 0.0666

            psarjstr = "{:.2f}".format(psarj2)
            ssarjstr = "{:.2f}".format(ssarj2)
            
            self.serialWrite("PSARJ=" + psarjstr + " ")
            self.serialWrite("SSARJ=" + ssarjstr + " ")
            self.serialWrite("PTRRJ=" + ptrrj + " ")
            self.serialWrite("STRRJ=" + strrj + " ")
            self.serialWrite("Beta1B=" + beta1b + " ")
            self.serialWrite("Beta1A=" + beta1a + " ")
            self.serialWrite("Beta2B=" + beta2b + " ")
            self.serialWrite("Beta2A=" + beta2a + " ")
            self.serialWrite("Beta3B=" + beta3b + " ")
            self.serialWrite("Beta3A=" + beta3a + " ")
            self.serialWrite("Beta4B=" + beta4b + " ")
            self.serialWrite("Beta4A=" + beta4a + " ")
            self.serialWrite("AOS=" + aos + " ")
	    self.serialWrite("Current1A=" + c1a + " ")
	    self.serialWrite("Current1B=" + c1b + " ")
	    self.serialWrite("Current3A=" + c3a + " ")
	    self.serialWrite("Current3B=" + c3b + " ")
       
        self.eps_screen.ids.psarj_value.text = psarj
        self.eps_screen.ids.ssarj_value.text = ssarj
        self.tcs_screen.ids.ptrrj_value.text = ptrrj
        self.tcs_screen.ids.strrj_value.text = strrj
        self.eps_screen.ids.beta1b_value.text = beta1b
        self.eps_screen.ids.beta1a_value.text = beta1a
        self.eps_screen.ids.beta2b_value.text = beta2b
        self.eps_screen.ids.beta2a_value.text = beta2a
        self.eps_screen.ids.beta3b_value.text = beta3b
        self.eps_screen.ids.beta3a_value.text = beta3a
        self.eps_screen.ids.beta4b_value.text = beta4b
        self.eps_screen.ids.beta4a_value.text = beta4a
        self.eps_screen.ids.c1a_value.text = c1a
        self.eps_screen.ids.v1a_value.text = v1a
        self.eps_screen.ids.c1b_value.text = c1b
        self.eps_screen.ids.v1b_value.text = v1b
        self.eps_screen.ids.c2a_value.text = c2a
        self.eps_screen.ids.v2a_value.text = v2a
        self.eps_screen.ids.c2b_value.text = c2b
        self.eps_screen.ids.v2b_value.text = v2b
        self.eps_screen.ids.c3a_value.text = c3a
        self.eps_screen.ids.v3a_value.text = v3a
        self.eps_screen.ids.c3b_value.text = c3b
        self.eps_screen.ids.v3b_value.text = v3b
        self.eps_screen.ids.c4a_value.text = c4a
        self.eps_screen.ids.v4a_value.text = v4a
        self.eps_screen.ids.c4b_value.text = c4b
        self.eps_screen.ids.v4b_value.text = v4b
        self.mimic_screen.ids.altitude_value.text = str(altitude) + " km"
        self.mimic_screen.ids.velocity_value.text = str(velocity) + " m/s"
        self.mimic_screen.ids.stationmass_value.text = str(iss_mass) + " kg"

        self.eva_screen.ids.EVA_needle.angle = float(self.map_rotation(0.0193368*float(crewlockpres)))
        self.eva_screen.ids.crewlockpressure_value.text = "{:.2f}".format(0.0193368*float(crewlockpres))
       
        psi_bar_x = self.map_psi_bar(0.0193368*float(crewlockpres)) #convert to torr
        
        self.eva_screen.ids.EVA_psi_bar.pos_hint = {"center_x": psi_bar_x, "center_y": 0.552} 
        
        if float(aos) == 1.00:
            self.changeColors(0,1,0)
            if self.root.current == 'mimic':
               fakeorbitboolean = False
               if mimicbutton == True:
                   switchtofake = False
            self.mimic_screen.ids.aosvalue.text = "Signal Acquired!"
        elif float(aos) == 0.00:
            self.changeColors(1,0,0)
            if self.root.current == 'mimic':
               fakeorbitboolean = True
            self.mimic_screen.ids.aosvalue.text = "Signal Lost"
        elif float(aos) == 2.00:
            self.changeColors(1,0.5,0)
            if self.root.current == 'mimic':
               fakeorbitboolean = True
            self.mimic_screen.ids.aosvalue.text = "Stale Signal!"

        if (mimicbutton == True and float(aos) == 1.00): 
             self.serialWrite("PSARJ=" + psarj + " ")
             self.serialWrite("SSARJ=" + ssarj + " ")
             self.serialWrite("PTRRJ=" + ptrrj + " ")
             self.serialWrite("STRRJ=" + strrj + " ")
             self.serialWrite("Beta1B=" + beta1b + " ")
             self.serialWrite("Beta1A=" + beta1a + " ")
             self.serialWrite("Beta2B=" + beta2b + " ")
             self.serialWrite("Beta2A=" + beta2a + " ")
             self.serialWrite("Beta3B=" + beta3b + " ")
             self.serialWrite("Beta3A=" + beta3a + " ")
             self.serialWrite("Beta4B=" + beta4b + " ")
             self.serialWrite("Beta4A=" + beta4a + " ")
             self.serialWrite("AOS=" + aos + " ")
	     self.serialWrite("Current1A=" + c1a + " ")
	     self.serialWrite("Current1B=" + c1b + " ")
	     self.serialWrite("Current3A=" + c3a + " ")
	     self.serialWrite("Current3B=" + c3b + " ")

#All GUI Screens are on separate kv files
Builder.load_file('MainScreen.kv')
Builder.load_file('Settings_Screen.kv')
Builder.load_file('FakeOrbitScreen.kv')
Builder.load_file('Orbit_Screen.kv')
Builder.load_file('EPS_Screen.kv')
Builder.load_file('CT_Screen.kv')
Builder.load_file('TCS_Screen.kv')
Builder.load_file('EVA_Screen.kv')
Builder.load_file('EVA_Pictures.kv')
Builder.load_file('Crew_Screen.kv')
Builder.load_file('ManualControlScreen.kv')
Builder.load_file('MimicScreen.kv')
Builder.load_file('CalibrateScreen.kv')

Builder.load_string('''
#:kivy 1.8
#:import kivy kivy
#:import win kivy.core.window
ScreenManager:
    MainScreen:
    Settings_Screen:
    FakeOrbitScreen:
    Orbit_Screen:
    EPS_Screen:
    CT_Screen:
    TCS_Screen:
    EVA_Screen:
    EVA_Pictures:
    Crew_Screen:
    ManualControlScreen:
    MimicScreen:
    CalibrateScreen:

<RotatedImage>:
    canvas.before:
        PushMatrix
        Rotate:
            angle: root.angle
            axis: 0,0,1
            origin: root.center
    canvas.after:
        PopMatrix
''')

if __name__ == '__main__':
    MainApp().run()
