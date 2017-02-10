import kivy
import urllib2
from neopixel import *
from bs4 import BeautifulSoup
from calendar import timegm
import datetime
import os
import sys
import json
import sqlite3
import serial
import sched, time
import smbus
import math
import time
from Naked.toolshed.shell import execute_js, muterun_js
import os
import signal
import multiprocessing, signal
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
from kivy.vector import Vector
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.floatlayout import FloatLayout
from kivy.event import EventDispatcher
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.stacklayout import StackLayout
from kivy.core.image import Image
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition, WipeTransition, SwapTransition

errorlog = open('errorlog.txt','w')
locationlog = open('locationlog.txt','a')

iss_crew_url = 'http://www.howmanypeopleareinspacerightnow.com/peopleinspace.json'        
nasaissurl = 'http://spaceflight.nasa.gov/realdata/sightings/SSapplications/Post/JavaSSOP/orbit/ISS/SVPOST.html'
req = urllib2.Request("http://api.open-notify.org/iss-now.json")
#crew_req = urllib2.Request("http://api.open-notify.org/astros.json")
TLE_req = urllib2.Request("http://spaceflight.nasa.gov/realdata/sightings/SSapplications/Post/JavaSSOP/orbit/ISS/SVPOST.html")

#LED_COUNT      = 7       # Number of LED pixels.
#LED_PIN        = 18      # GPIO pin connected to the pixels (must support PWM!).
#LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
#LED_DMA        = 5       # DMA channel to use for generating signal (try 5)
#LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
#LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift

#strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
# Intialize the library (must be called once before other functions).
#strip.begin()

#for i in range(strip.numPixels()):
#    strip.setPixelColor(i, Color(255,255,255))
#    strip.show()
#    time.sleep(0.1)

try:
    ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=0)
except:
    print "No serial connection detected - GPIO"
    errorlog.write(str(datetime.datetime.utcnow()))
    errorlog.write(' ')
    errorlog.write("serial connection GPIO not found")
    errorlog.write('\n')

try:
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=0)
except:
    print "No serial connection detected - USB"
    errorlog.write(str(datetime.datetime.utcnow()))
    errorlog.write(' ')
    errorlog.write("serial connection USB not found")
    errorlog.write('\n')

crewjsonsuccess = False
mimicbutton = False
fakeorbitboolean = False
zerocomplete = False
switchtofake = False
manualcontrol = False
startup = True
isscrew = 0

conn = sqlite3.connect('iss_telemetry.db') #sqlite database call change to include directory
c = conn.cursor() 
val = ""
       
psarj2 = 1.0
ssarj2 = 1.0

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
position_x = 0.00
position_y = 0.00
position_z = 0.00
velocity_x = 0.00
velocity_y = 0.00
velocity_z = 0.00
velocity = 0.00
altitude = 0.00
mass = 0.00

def StringToBytes(val):
    retVal = []
    for c in val:
            retVal.append(ord(c))
    return retVal

class MainScreen(Screen):
    def changeManualControlBoolean(self, *args):
        global manualcontrol
        manualcontrol = args[0]
        
class CalibrateScreen(Screen):
    def serialWrite(self, *args):
        try:
            self.serialActualWrite(self, *args)
        except:
            errorlog.write(str(datetime.datetime.utcnow()))
            errorlog.write(' ')
            errorlog.write("Attempted write - no serial device connected")
            errorlog.write('\n')

    def serialActualWrite(self, *args):
        ser.write(*args)

    def zeroJoints(self):
        self.changeBoolean(True)
        ser.write('Zero')

    def changeBoolean(self, *args):
        global zerocomplete
        zerocomplete = args[0]

class ManualControlScreen(Screen):
    def incrementPSARJ(self, *args):
        global psarjmc
        psarjmc += args[0]
        self.serialWrite("PSARJ=" + str(psarjmc) + " ")   
     
    def incrementSSARJ(self, *args):
        global ssarjmc
        ssarjmc += args[0]
        self.serialWrite("SSARJ=" + str(ssarjmc) + " ")   
     
    def incrementPTTRJ(self, *args):
        global ptrrjmc
        ptrrjmc += args[0]
        self.serialWrite("PTRRJ=" + str(ptrrjmc) + " ")   
     
    def incrementSTRRJ(self, *args):
        global strrjmc
        strrjmc += args[0]
        self.serialWrite("STRRJ=" + str(strrjmc) + " ")   
     
    def incrementBeta1B(self, *args):
        global beta1bmc
        beta1bmc += args[0]
        self.serialWrite("Beta1B=" + str(beta1bmc) + " ")   
     
    def incrementBeta1A(self, *args):
        global beta1amc
        beta1amc += args[0]
        self.serialWrite("Beta1A=" + str(beta1amc) + " ")   
     
    def incrementBeta2B(self, *args):
        global beta2bmc
        beta2bmc += args[0]
        self.serialWrite("Beta2B=" + str(beta2bmc) + " ")   
     
    def incrementBeta2A(self, *args):
        global beta2amc
        beta2amc += args[0]
        self.serialWrite("Beta2A=" + str(beta2amc) + " ")   
     
    def incrementBeta3B(self, *args):
        global beta3bmc
        beta3bmc += args[0]
        self.serialWrite("Beta3B=" + str(beta3bmc) + " ")   
     
    def incrementBeta3A(self, *args):
        global beta3amc
        beta3amc += args[0]
        self.serialWrite("Beta3A=" + str(beta3amc) + " ")   
     
    def incrementBeta4B(self, *args):
        global beta4bmc
        beta4bmc += args[0]
        self.serialWrite("Beta4B=" + str(beta4bmc) + " ")   
     
    def incrementBeta4A(self, *args):
        global beta4amc
        beta4amc += args[0]
        self.serialWrite("Beta4A=" + str(beta4amc) + " ")   
     
    def changeBoolean(self, *args):
        global manualcontrol
        manualcontrol = args[0]
    
    def serialWrite(self, *args):
        try:
            self.serialActualWrite(self, *args)
        except:
            errorlog.write(str(datetime.datetime.utcnow()))
            errorlog.write(' ')
            errorlog.write("Attempted write - no serial device connected")
            errorlog.write('\n')

    def serialActualWrite(self, *args):
        ser.write(*args)

class FakeOrbitScreen(Screen):
    def serialWrite(self, *args):
        try:
            self.serialActualWrite(self, *args)
        except:
            errorlog.write(str(datetime.datetime.utcnow()))
            errorlog.write(' ')
            errorlog.write("Attempted write - no serial device connected")
            errorlog.write('\n')

    def serialActualWrite(self, *args):
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

def point_inside_polygon(x, y, poly):
    n = len(poly)
    inside = False
    p1x = poly[0]
    p1y = poly[1]
    for i in range(0, n + 2, 2):
        p2x = poly[i % n]
        p2y = poly[(i + 1) % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

class TriangleButton(ButtonBehavior, Widget):
    triangle_color = ListProperty([1,0,0,1])
    p1 = ListProperty([0, 0])
    p2 = ListProperty([0, 0])
    p3 = ListProperty([0, 0])

    def changecolordown(self, *args):
        self.triangle_color = (1,0,1,1)

    def changecolorup(self, *args):
        self.triangle_color = (1,0,0,1)

    def collide_point(self, x, y):
        x, y = self.to_local(x, y)
        return point_inside_polygon(x, y,
                self.p1 + self.p2 + self.p3) 

class MainApp(App):

    def build(self):
        global startup
        global crewjsonsuccess
        self.mimic_screen = MimicScreen(name = 'mimic')
        self.fakeorbit_screen = FakeOrbitScreen(name = 'fakeorbit')
        self.orbit_screen = Orbit_Screen(name = 'orbit')
        self.eps_screen = EPS_Screen(name = 'eps')
        self.ct_screen = CT_Screen(name = 'ct')
        self.tcs_screen = TCS_Screen(name = 'tcs')
        self.crew_screen = Crew_Screen(name = 'crew')
        self.settings_screen = Settings_Screen(name = 'settings')

        root = MainScreenManager(transition=WipeTransition())
        root.add_widget(MainScreen(name = 'main'))
        root.add_widget(CalibrateScreen(name = 'calibrate'))
        root.add_widget(self.mimic_screen)
        root.add_widget(self.fakeorbit_screen)
        root.add_widget(self.orbit_screen)
        root.add_widget(self.eps_screen)
        root.add_widget(self.ct_screen)
        root.add_widget(self.tcs_screen)
        root.add_widget(self.crew_screen)
        root.add_widget(self.settings_screen)
        root.add_widget(ManualControlScreen(name = 'manualcontrol'))
        root.current= 'main'
    
        Clock.schedule_interval(self.update_labels, 1)
        Clock.schedule_interval(self.checkAOSlong, 5)
        Clock.schedule_interval(self.checkCrew, 3600)
        if crewjsonsuccess == False:
            Clock.schedule_once(self.checkCrew, 10)
        if startup == True:
            startup = False
            #self.checkCrew(60)

        Clock.schedule_interval(self.getTLE, 3600)
        return root

    def serialWrite(self, *args):
        try:
            self.serialActualWrite(self, *args)
        except:
            errorlog.write(str(datetime.datetime.utcnow()))
            errorlog.write(' ')
            errorlog.write("Attempted write - no serial device connected")
            errorlog.write('\n')

    def serialActualWrite(self, *args):
        ser.write(*args)

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
        req = urllib2.Request(iss_crew_url, headers={'User-Agent' : "Magic Browser"})
        stuff = urllib2.urlopen(req)
        crewmember = ['','','','','','','','','','','','']
        crewmemberbio = ['','','','','','','','','','','','']
        crewmembertitle = ['','','','','','','','','','','','']
        crewmemberlaunchdate = ['','','','','','','','','','','','']
        crewmemberpicture = ['','','','','','','','','','','','']
        crewmembercountry = ['','','','','','','','','','','','']

        if (stuff.info().getsubtype()=='json'):
            print "JSON true"
            crewjsonsuccess = True
            data = json.load(stuff)
            number_of_space = int(data['number'])
            for num in range(1,number_of_space+1):
                if(str(data['people'][num-1]['location']) == str("International Space Station")):
                    crewmember[isscrew] = str(data['people'][num-1]['name'])
                    crewmemberbio[isscrew] = (data['people'][num-1]['bio'])
                    crewmembertitle[isscrew] = str(data['people'][num-1]['title'])
                    crewmemberlaunchdate[isscrew] = str(data['people'][num-1]['launchdate'])
                    crewmemberpicture[isscrew] = str(data['people'][num-1]['biophoto'])
                    crewmembercountry[isscrew] = str(data['people'][num-1]['country']).title()
                    if(str(data['people'][num-1]['country'])==str('usa')):
                        crewmembercountry[isscrew] = str('USA')
                    isscrew = isscrew+1  
        else:
            print "JSON false"
            crewjsonsuccess = False

        self.crew_screen.ids.crew1.text = crewmember[0]  
        self.crew_screen.ids.crew1title.text = crewmembertitle[0]  
        self.crew_screen.ids.crew1bio.text = crewmemberbio[0]  
        self.crew_screen.ids.crew1country.text = crewmembercountry[0]  
        #self.crew_screen.ids.crew1image.source = str(crewmemberpicture[0])
        self.crew_screen.ids.crew2.text = crewmember[1]  
        self.crew_screen.ids.crew3.text = crewmember[2]  
        self.crew_screen.ids.crew4.text = crewmember[3]  
        self.crew_screen.ids.crew5.text = crewmember[4]  
        self.crew_screen.ids.crew6.text = crewmember[5]  
        self.crew_screen.ids.crew7.text = crewmember[6]  
        self.crew_screen.ids.crew8.text = crewmember[7]  
        self.crew_screen.ids.crew9.text = crewmember[8]  
        self.crew_screen.ids.crew10.text = crewmember[9]  
        self.crew_screen.ids.crew11.text = crewmember[10]  
        self.crew_screen.ids.crew12.text = crewmember[11]  
        
    def checkAOSlong(self, dt):
        global aos
        if float(aos) == 0.00:
            print "signal lost - writing longitude"
            response = urllib2.urlopen(req)
            obj = json.loads(response.read())
            locationlog.write("time ")
            locationlog.write(str(obj['timestamp']))
            locationlog.write(" long ")
            locationlog.write(str(obj['iss_position']['longitude']))
            locationlog.write('\n')
    
    def update_labels(self, dt):
        global mimicbutton
        global switchtofake
        global fakeorbitboolean
        global psarj2
        global ssarj2
        global manualcontrol
        global psarj
        global ssarj
        global ptrrj
        global strrj
        global beta1b
        global beta1a
        global beta2b
        global beta2a
        global beta3b
        global beta3a
        global beta4b
        global beta4a
        global aos
        global los
        global oldLOS
        global psarjmc
        global ssarjmc
        global ptrrjmc
        global strrjmc
        global beta1bmc
        global beta1amc
        global beta2bmc
        global beta2amc
        global beta3bmc
        global beta3amc
        global beta4bmc
        global beta4amc
        global EVAinProgress
        global position_x
        global position_y
        global position_z
        global velocity_x
        global velocity_y
        global velocity_z
        global altitude
        global velocity
        global iss_mass     
 
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
        crewlockpres = "{:.2f}".format(float((values[16])[0]))
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
        
        if float(crewlockpres) < 500:
            EVAinProgress = True
            self.mimic_screen.ids.EVa_value.text = "EVA in Progress!!!"
            self.mimic_screen.ids.EVa_value.color = 0,1,0
        else:
            EVAinProgress = False 
            self.mimic_screen.ids.EVa_value.text = ""
            self.mimic_screen.ids.EVa_value.color = 0,0,0

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
        self.mimic_screen.ids.difference.text = str(difference)
        self.mimic_screen.ids.altitude_value.text = str(altitude) + " km"
        self.mimic_screen.ids.velocity_value.text = str(velocity) + " m/s"
        self.mimic_screen.ids.stationmass_value.text = str(iss_mass) + " kg"

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
    Crew_Screen:
    ManualControlScreen:
    MimicScreen:
    CalibrateScreen:

<MainScreen>:
    name: 'main'
    FloatLayout:
        orientation: 'vertical'
        Image:
            source: './imgs/iss.png'
            allow_stretch: True
            keep_ratio: True
        Label:
            text: 'ISS Mimic'
            bold: True
            font_size: 120
            markup: True
            height: "20dp"
            color: 1,0,1
            width: "100dp"
        Label:
            text: 'Mimic screen disabled until calibration is performed'
            bold: True
            pos_hint: {"center_x": 0.5, "center_y": 0.3}
            font_size: 20
            markup: True
            height: "20dp"
            color: 1,0,1
            width: "100dp"
        Button:
            size_hint: 0.3,0.1
            pos_hint: {"center_x": 0.2, "center_y": 0.9}
            text: 'Fake Orbit'
            font_size: 30
            width: 50
            height: 20
            on_release: root.manager.current = 'fakeorbit'
        Button:
            size_hint: 0.1,0.15
            pos_hint: {"center_x": 0.9, "center_y": 0.9}
            background_normal: './imgs/Settings_Icon.png'
            text: ''
            on_release: root.manager.current = 'settings'
        BoxLayout:
            size_hint_y: None
            Button:
                text: 'Control'
                font_size: 30
                width: 50
                height: 20
                on_press: root.changeManualControlBoolean(True)
                on_release: root.manager.current = 'manualcontrol'
            Button:
                text: 'Calibrate'
                font_size: 30
                width: 50
                height: 20
                on_release: root.manager.current = 'calibrate'
                on_release: my_button.disabled = False
            MyButton:
                id: my_button
                text: 'Mimic'
                disabled: True
                font_size: 30
                width: 50
                height: 20
                on_release: app.root.current = 'mimic'
            Button:
                text: 'Exit'
                font_size: 30
                width: 50
                height: 20
                on_release: app.stop(*args)
<Settings_Screen>:
    name: 'settings'
    FloatLayout:
        orientation: 'vertical'
        Image:
            source: './imgs/iss.png'
            allow_stretch: True
            keep_ratio: True
        Label:
            text: 'Settings'
            bold: True
            font_size: 120
            markup: True
            height: "20dp"
            color: 1,0,1
            width: "100dp"
        Button:
            size_hint: 0.3,0.1
            pos_hint: {"Left": 1, "Bottom": 1}
            text: 'Return'
            font_size: 30
            on_release: root.manager.current = 'main'
<FakeOrbitScreen>:
    name: 'fakeorbit'
    FloatLayout:
        orientation: 'vertical'
        Image:
            source: './imgs/iss2.png'
            allow_stretch: True
            keep_ratio: True
        Label:
            id: fakeorbitstatus
            pos_hint: {"center_x": 0.25, "center_y": 0.85}
            text: 'Status'
            markup: True
            color: 1,0,1
            font_size: 60
        Label:
            id: fakepsarj_label
            pos_hint: {"center_x": 0.6, "center_y": 0.5}
            text: 'PSARJ:'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: fakepsarj_value
            pos_hint: {"center_x": 0.8, "center_y": 0.5}
            text: '0.000'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: fakessarj_label
            pos_hint: {"center_x": 0.6, "center_y": 0.35}
            text: 'SSARJ:'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: fakessarj_value
            pos_hint: {"center_x": 0.8, "center_y": 0.35}
            text: '0.000'
            markup: True
            color: 1,1,1
            font_size: 30
        Button:
            id: orbitstartbutton
            size_hint: 0.25,0.1
            pos_hint: {"x": 0.07, "y": 0.6}
            text: 'Start'
            disabled: False
            font_size: 30
            on_release: fakeorbitstatus.text = 'Sending...'
            on_release: root.changeBoolean(True)
            on_release: orbitstopbutton.disabled = False
            on_release: orbitstartbutton.disabled = True
        Button:
            id: orbitstopbutton
            size_hint: 0.25,0.1
            pos_hint: {"x": 0.07, "y": 0.4}
            text: 'Stop'
            disabled: True
            font_size: 30
            on_release: fakeorbitstatus.text = 'Stopped'
            on_release: root.changeBoolean(False)
            on_release: orbitstopbutton.disabled = True
            on_release: orbitstartbutton.disabled = False
        Button:
            size_hint: 0.3,0.1
            pos_hint: {"Left": 1, "Bottom": 1}
            text: 'Return'
            font_size: 30
            on_release: root.changeBoolean(False)
            on_release: root.manager.current = 'main'
           
<ManualControlScreen>:
    name: 'manualcontrol'
    FloatLayout:
        Image:
            source: './imgs/iss_calibrate.png'
            allow_stretch: True
            keep_ratio: False
        Label:
            size_hint: None,None
            text: '1B'
            pos_hint: {'x': 0.035, 'y': 0.73}
            font_size: 30
            markup: True
            color: 0,0,0,1
            halign: 'center'
            valign: 'middle'
        TriangleButton:
            id: t1Bup
            p1: root.width*0.060, root.height*0.86
            p2: root.width*0.095, root.height*0.96
            p3: root.width*0.130, root.height*0.86
            on_press: self.changecolordown()
            on_release: root.incrementPSARJ(1)
            on_release: self.changecolorup()
        TriangleButton:
            id: t1Bdown
            p1: root.width*0.060, root.height*0.8
            p2: root.width*0.095, root.height*0.7
            p3: root.width*0.130, root.height*0.8
            on_press: self.changecolordown()
            on_release: root.incrementPSARJ(-1)
            on_release: self.changecolorup()
        Label:
            size_hint: None,None
            text: '3B'
            pos_hint: {'x': 0.035, 'y': 0.25}
            markup: True
            color: 0,0,0,1
            font_size: 30
            halign: 'center'
        TriangleButton:
            id: t3Bup
            p1: root.width*0.060, root.height*0.38
            p2: root.width*0.095, root.height*0.48
            p3: root.width*0.130, root.height*0.38
            on_press: self.changecolordown()
            on_release: root.incrementBeta3B(1)
            on_release: self.changecolorup()
        TriangleButton:
            id: t3Bdown
            p1: root.width*0.060, root.height*0.32
            p2: root.width*0.095, root.height*0.22
            p3: root.width*0.130, root.height*0.32
            on_press: self.changecolordown()
            on_release: root.incrementBeta3B(-1)
            on_release: self.changecolorup()
        Label:
            size_hint: None,None
            text: '3A'
            pos_hint: {'x': .155, 'y': .73}
            markup: True
            color: 0,0,0,1
            font_size: 30
            halign: 'center'
        TriangleButton:
            id: t3Aup
            p1: root.width*0.180, root.height*0.86
            p2: root.width*0.215, root.height*0.96
            p3: root.width*0.250, root.height*0.86
            on_press: self.changecolordown()
            on_release: root.incrementBeta3A(1)
            on_release: self.changecolorup()
        TriangleButton:
            id: t3Adown
            p1: root.width*0.180, root.height*0.8
            p2: root.width*0.215, root.height*0.7
            p3: root.width*0.250, root.height*0.8
            on_press: self.changecolordown()
            on_release: root.incrementBeta3A(-1)
            on_release: self.changecolorup()
        Label:
            size_hint: None,None
            text: '1A'
            pos_hint: {'x': .155, 'y': .25}
            markup: True
            color: 0,0,0,1
            font_size: 30
            halign: 'center'
        TriangleButton:
            id: t1Aup
            p1: root.width*0.180, root.height*0.38
            p2: root.width*0.215, root.height*0.48
            p3: root.width*0.250, root.height*0.38
            on_press: self.changecolordown()
            on_release: root.incrementBeta1A(1)
            on_release: self.changecolorup()
        TriangleButton:
            id: t1Adown
            p1: root.width*0.180, root.height*0.32
            p2: root.width*0.215, root.height*0.22
            p3: root.width*0.250, root.height*0.32
            on_press: self.changecolordown()
            on_release: root.incrementBeta1A(-1)
            on_release: self.changecolorup()
        Label:
            size_hint: None,None
            text: 'SSARJ'
            pos_hint: {'x': .275, 'y': .5}
            markup: True
            color: 0,0,0,1
            font_size: 30
            halign: 'center'
        TriangleButton:
            id: SSARJup
            p1: root.width*0.300, root.height*0.65
            p2: root.width*0.335, root.height*0.75
            p3: root.width*0.370, root.height*0.65
            on_press: self.changecolordown()
            on_release: root.incrementSSARJ(1)
            on_release: self.changecolorup()
        TriangleButton:
            id: SSARJdown
            p1: root.width*0.300, root.height*0.55
            p2: root.width*0.335, root.height*0.45
            p3: root.width*0.370, root.height*0.55
            on_press: self.changecolordown()
            on_release: root.incrementSSARJ(-1)
            on_release: self.changecolorup()
        Label:
            size_hint: None,None
            text: 'STTRJ'
            pos_hint: {'x': .445, 'y': .55}
            markup: True
            color: 0,0,0,1
            font_size: 30
            halign: 'center'
            valign: 'middle'
        TriangleButton:
            id: STTRJup
            p1: root.width*0.480, root.height*0.800
            p2: root.width*0.420, root.height*0.750
            p3: root.width*0.480, root.height*0.700
            on_press: self.changecolordown()
            on_release: root.incrementSTRRJ(1)
            on_release: self.changecolorup()
        TriangleButton:
            id: STTRJdown
            p1: root.width*0.520, root.height*0.800
            p2: root.width*0.580, root.height*0.750
            p3: root.width*0.520, root.height*0.700
            on_press: self.changecolordown()
            on_release: root.incrementSTRRJ(-1)
            on_release: self.changecolorup()
        Label:
            size_hint: None,None
            text: 'PTTRJ'
            pos_hint: {'x': .445, 'y': .45}
            markup: True
            color: 0,0,0,1
            font_size: 30
            halign: 'center'
        TriangleButton:
            id: PTTRJup
            p1: root.width*0.480, root.height*0.400
            p2: root.width*0.420, root.height*0.450
            p3: root.width*0.480, root.height*0.500
            on_press: self.changecolordown()
            on_release: root.incrementPTRRJ(1)
            on_release: self.changecolorup()
        TriangleButton:
            id: PTTRJdown
            p1: root.width*0.520, root.height*0.400
            p2: root.width*0.580, root.height*0.450
            p3: root.width*0.520, root.height*0.500
            on_press: self.changecolordown()
            on_release: root.incrementPTRRJ(-1)
            on_release: self.changecolorup()
        Label:
            size_hint: None,None
            text: 'PSARJ'
            pos_hint: {'x': .6, 'y': .5}
            markup: True
            color: 0,0,0,1
            font_size: 30
            halign: 'center'
        TriangleButton:
            id: PSARJup
            p1: root.width*0.700, root.height*0.65
            p2: root.width*0.665, root.height*0.75
            p3: root.width*0.630, root.height*0.65
            on_press: self.changecolordown()
            on_release: root.incrementPSARJ(1)
            on_release: self.changecolorup()
        TriangleButton:
            id: PSARJdown
            p1: root.width*0.700, root.height*0.55
            p2: root.width*0.665, root.height*0.45
            p3: root.width*0.630, root.height*0.55
            on_press: self.changecolordown()
            on_release: root.incrementPSARJ(-1)
            on_release: self.changecolorup()
        Label:
            size_hint: None,None
            text: '2A'
            pos_hint: {'x': .725, 'y': .73}
            markup: True
            color: 0,0,0,1
            font_size: 30
            halign: 'center'
        TriangleButton:
            id: t2Aup
            p1: root.width*0.820, root.height*0.86
            p2: root.width*0.785, root.height*0.96
            p3: root.width*0.750, root.height*0.86
            on_press: self.changecolordown()
            on_release: root.incrementBeta2A(1)
            on_release: self.changecolorup()
        TriangleButton:
            id: t2Adown
            p1: root.width*0.820, root.height*0.8
            p2: root.width*0.785, root.height*0.7
            p3: root.width*0.750, root.height*0.8
            on_press: self.changecolordown()
            on_release: root.incrementBeta2A(-1)
            on_release: self.changecolorup()
        Label:
            size_hint: None,None
            text: '4A'
            pos_hint: {'x': .725, 'y': .25}
            markup: True
            color: 0,0,0,1
            font_size: 30
            halign: 'center'
        TriangleButton:
            id: t4Aup
            p1: root.width*0.820, root.height*0.38
            p2: root.width*0.785, root.height*0.48
            p3: root.width*0.750, root.height*0.38
            on_press: self.changecolordown()
            on_release: root.incrementBeta4A(1)
            on_release: self.changecolorup()
        TriangleButton:
            id: t4Adown
            p1: root.width*0.820, root.height*0.32
            p2: root.width*0.785, root.height*0.22
            p3: root.width*0.750, root.height*0.32
            on_press: self.changecolordown()
            on_release: root.incrementBeta4A(-1)
            on_release: self.changecolorup()
        Label:
            size_hint: None,None
            text: '4B'
            pos_hint: {'x': .84, 'y': .73}
            markup: True
            color: 0,0,0,1
            font_size: 30
            halign: 'center'
        TriangleButton:
            id: t4Bup
            p1: root.width*0.940, root.height*0.86
            p2: root.width*0.905, root.height*0.96
            p3: root.width*0.870, root.height*0.86
            on_press: self.changecolordown()
            on_release: root.incrementBeta4B(1)
            on_release: self.changecolorup()
        TriangleButton:
            id: t4Bdown
            p1: root.width*0.940, root.height*0.8
            p2: root.width*0.905, root.height*0.7
            p3: root.width*0.870, root.height*0.8
            on_press: self.changecolordown()
            on_release: root.incrementBeta4B(-1)
            on_release: self.changecolorup()
        Label:
            size_hint: None,None
            text: '2B'
            pos_hint: {'x': .84, 'y': .25}
            markup: True
            color: 0,0,0,1
            font_size: 30
            halign: 'center'
        TriangleButton:
            id: t2Bup
            p1: root.width*0.940, root.height*0.38
            p2: root.width*0.905, root.height*0.48
            p3: root.width*0.870, root.height*0.38
            on_press: self.changecolordown()
            on_release: root.incrementBeta2B(1)
            on_release: self.changecolorup()
        TriangleButton:
            id: t2Bdown
            p1: root.width*0.940, root.height*0.32
            p2: root.width*0.905, root.height*0.22
            p3: root.width*0.870, root.height*0.32
            on_press: self.changecolordown()
            on_release: root.incrementBeta2B(-1)
            on_release: self.changecolorup()
        Button:
            size_hint: 0.3,0.1
            pos_hint: {"center_x": 0.5, "Bottom": 1}
            text: 'Return'
            font_size: 30
            on_press: root.changeBoolean(False)
            on_release: root.manager.current = 'main'
            
<CalibrateScreen>:
    name: 'calibrate'
    FloatLayout:
        orientation: 'vertical'
        Image:
            source: './imgs/iss_calibrate.png'
            allow_stretch: False
            keep_ratio: False
        Label:
            pos_hint: {"center_x": 0.5, "center_y": 0.95}
            id: calibratestatus
            text: 'Calibrate ISS Angles'
            color: 0,0,0,1
            font_size: 40
        Button:
            id: zerobutton
            size_hint: 0.4,0.1
            pos_hint: {"center_x": 0.5, "center_y": 0.5}
            text: 'Zero All Angles'
            font_size: 30
            on_press: root.zeroJoints()
            on_release: calibratestatus.text = 'Angles Zero-ing!'
        Button:
            size_hint: 0.3,0.1
            pos_hint: {"center_x": 0.5, "Bottom": 1}
            text: 'Return'
            font_size: 30
            on_release: root.manager.current = 'main'
<CT_Screen>:
    name: 'ct'
    FloatLayout:
        Image:
            source: './imgs/iss2.png'
            allow_stretch: True
            keep_ratio: False
        Label:
            pos_hint: {"center_x": 0.15, "center_y": 0.8}
            text: 'C&T Stuff'
            markup: True
            color: 1,0,1
            font_size: 30
        Button:
            size_hint: 0.3,0.1
            pos_hint: {"Left": 1, "Bottom": 1}
            text: 'Return'
            font_size: 30
            on_release: app.root.current = 'mimic'
<Orbit_Screen>:
    name: 'orbit'
    FloatLayout:
        Image:
            source: './imgs/iss2.png'
            allow_stretch: True
            keep_ratio: False
        Label:
            pos_hint: {"center_x": 0.15, "center_y": 0.8}
            text: 'Orbit Stuff'
            markup: True
            color: 1,0,1
            font_size: 30
        Button:
            size_hint: 0.3,0.1
            pos_hint: {"Left": 1, "Bottom": 1}
            text: 'Return'
            font_size: 30
            on_release: app.root.current = 'mimic'
<TCS_Screen>:
    name: 'tcs'
    FloatLayout:
        Image:
            source: './imgs/iss2.png'
            allow_stretch: True
            keep_ratio: False
        Label:
            pos_hint: {"center_x": 0.15, "center_y": 0.8}
            text: 'TCS Stuff'
            markup: True
            color: 1,0,1
            font_size: 30
        Label:
            id: ptrrj_label
            pos_hint: {"center_x": 0.6, "center_y": 0.78}
            text: 'PTRRJ:'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: ptrrj_value
            pos_hint: {"center_x": 0.8, "center_y": 0.78}
            text: '0.003'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: strrj_label
            pos_hint: {"center_x": 0.6, "center_y": 0.71}
            text: 'STRRJ:'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: strrj_value
            pos_hint: {"center_x": 0.8, "center_y": 0.71}
            text: '0.003'
            markup: True
            color: 1,1,1
            font_size: 30
        Button:
            size_hint: 0.3,0.1
            pos_hint: {"Left": 1, "Bottom": 1}
            text: 'Return'
            font_size: 30
            on_release: app.root.current = 'mimic'
<Crew_Screen>:
    name: 'crew'
    FloatLayout:
        Image:
            source: './imgs/iss1.png'
            allow_stretch: True
            keep_ratio: False
        Button:
            size_hint: 0.3,0.1
            pos_hint: {"Left": 1, "Bottom": 1}
            text: 'Return'
            font_size: 30
            on_release: app.root.current = 'mimic'
        Label:
            id: crew1
            pos_hint: {"center_x": 0.15, "center_y": 0.90}
            halign: 'center'
            valign: 'middle'
            text: ''
            markup: True
            color: 1,0,1
            font_size: 25
        Label:
            id: crew1title
            pos_hint: {"center_x": 0.15, "center_y": 0.83}
            halign: 'center'
            valign: 'middle'
            text: ''
            markup: True
            color: 1,1,1
            font_size: 20
        Label:
            id: crew1country
            pos_hint: {"center_x": 0.15, "center_y": 0.76}
            markup: True
            halign: 'center'
            valign: 'middle'
            text: ''
            color: 1,1,1
            font_size: 18
        Label:
            id: crew1bio
            pos_hint: {"center_x": 0.2, "center_y": 0.5}
            text_size: cm(8), cm(5)
            markup: True
            halign: 'center'
            valign: 'middle'
            text: ''
            color: 1,1,1
            font_size: 18
        Image:
            id: crew1image
            source: 'http://www.howmanypeopleareinspacerightnow.com/app/flags/flag-usa.jpg'
            pos_hint: {"center_x": 0.5, "center_y": 0.5}
            keep_ratio: True
            size_hint: 0.3, 0.4

        Label:
            id: crew2
            pos_hint: {"center_x": 0.1, "center_y": 0.2}
            text: ''
            markup: True
            color: 1,0,1
            font_size: 25
        Label:
            id: crew3
            pos_hint: {"center_x": 0.1, "center_y": 0.2}
            text: ''
            markup: True
            color: 1,0,1
            font_size: 25
        Label:
            id: crew4
            pos_hint: {"center_x": 0.1, "center_y": 0.2}
            text: ''
            markup: True
            color: 1,0,1
            font_size: 25
        Label:
            id: crew5
            pos_hint: {"center_x": 0.1, "center_y": 0.2}
            text: ''
            markup: True
            color: 1,0,1
            font_size: 25
        Label:
            id: crew6
            pos_hint: {"center_x": 0.1, "center_y": 0.15}
            text: ''
            markup: True
            color: 1,0,1
            font_size: 25
            
        Label:
            id: crew7
            pos_hint: {"center_x": 0.1, "center_y": 0.15}
            text: ''
            markup: True
            color: 1,0,1
            font_size: 25
            
        Label:
            id: crew8
            pos_hint: {"center_x": 0.1, "center_y": 0.15}
            text: ''
            markup: True
            color: 1,0,1
            font_size: 25
            
        Label:
            id: crew9
            pos_hint: {"center_x": 0.1, "center_y": 0.15}
            text: ''
            markup: True
            color: 1,0,1
            font_size: 25
            
        Label:
            id: crew10
            pos_hint: {"center_x": 0.1, "center_y": 0.15}
            text: ''
            markup: True
            color: 1,0,1
            font_size: 25
            
        Label:
            id: crew11
            pos_hint: {"center_x": 0.1, "center_y": 0.15}
            text: ''
            markup: True
            color: 1,0,1
            font_size: 25
            
        Label:
            id: crew12
            pos_hint: {"center_x": 0.1, "center_y": 0.15}
            text: ''
            markup: True
            color: 1,0,1
            font_size: 25
<EPS_Screen>:
    name: 'eps'
    FloatLayout:
        Image:
            source: './imgs/iss1.png'
            allow_stretch: True
            keep_ratio: False
        Button:
            size_hint: 0.3,0.1
            pos_hint: {"Left": 1, "Bottom": 1}
            text: 'Return'
            font_size: 30
            on_release: app.root.current = 'mimic'
        Label:
            id: psarj_label
            pos_hint: {"center_x": 0.35, "center_y": 0.55}
            text: 'PSARJ:'
            markup: True
            color: 1,1,1
            font_size: 25
        Label:
            id: psarj_value
            pos_hint: {"center_x": 0.35, "center_y": 0.48}
            text: '0.003'
            markup: True
            color: 1,1,1
            font_size: 25
        Label:
            id: ssarj_label
            pos_hint: {"center_x": 0.65, "center_y": 0.55}
            text: 'SSARJ:'
            markup: True
            color: 1,1,1
            font_size: 25
        Label:
            id: ssarj_value
            pos_hint: {"center_x": 0.65, "center_y": 0.48}
            text: '0.003'
            markup: True
            color: 1,1,1
            font_size: 25
            
        Label:
            pos_hint: {"center_x": 0.62, "center_y": 0.85}
            text: 'Channel 1A'
            markup: True
            color: 1,0,1
            font_size: 30
        Label:
            id: beta1a_label
            pos_hint: {"center_x": 0.57, "center_y": 0.78}
            text: 'Angle:'
            markup: True
            color: 1,1,1
            font_size: 20
        Label:
            id: beta1a_value
            pos_hint: {"center_x": 0.67, "center_y": 0.78}
            text: '0.003'
            markup: True
            color: 1,1,1
            font_size: 20
        Label:
            id: c1a_label
            pos_hint: {"center_x": 0.57, "center_y": 0.71}
            text: 'Current:'
            markup: True
            color: 1,1,1
            font_size: 20
        Label:
            id: c1a_value
            pos_hint: {"center_x": 0.67, "center_y": 0.71}
            text: '0.003'
            markup: True
            color: 1,1,1
            font_size: 20
        Label:
            id: v1a_label
            pos_hint: {"center_x": 0.57, "center_y": 0.64}
            text: 'Voltage:'
            markup: True
            color: 1,1,1
            font_size: 20
        Label:
            id: v1a_value
            pos_hint: {"center_x": 0.67, "center_y": 0.64}
            text: '0.003'
            markup: True
            color: 1,1,1
            font_size: 20
            
        Label:
            pos_hint: {"center_x": 0.87, "center_y": 0.38}
            text: 'Channel 1B'
            markup: True
            color: 1,0,1
            font_size: 30
        Label:
            id: beta1b_label
            pos_hint: {"center_x": 0.82, "center_y": 0.31}
            text: 'Angle:'
            markup: True
            color: 1,1,1
            font_size: 20
        Label:
            id: beta1b_value
            pos_hint: {"center_x": 0.92, "center_y": 0.31}
            text: '0.003'
            markup: True
            color: 1,1,1
            font_size: 20
        Label:
            id: c1b_label
            pos_hint: {"center_x": 0.82, "center_y": 0.24}
            text: 'Current:'
            markup: True
            color: 1,1,1
            font_size: 20
        Label:
            id: c1b_value
            pos_hint: {"center_x": 0.92, "center_y": 0.24}
            text: '0.003'
            markup: True
            color: 1,1,1
            font_size: 20
        Label:
            id: v1b_label
            pos_hint: {"center_x": 0.82, "center_y": 0.17}
            text: 'Voltage:'
            markup: True
            color: 1,1,1
            font_size: 20
        Label:
            id: v1b_value
            pos_hint: {"center_x": 0.92, "center_y": 0.17}
            text: '0.003'
            markup: True
            color: 1,1,1
            font_size: 20

        Label:
            pos_hint: {"center_x": 0.37, "center_y": 0.38}
            text: 'Channel 2A'
            markup: True
            color: 1,0,1
            font_size: 30
        Label:
            id: beta2a_label
            pos_hint: {"center_x": 0.32, "center_y": 0.31}
            text: 'Angle:'
            markup: True
            color: 1,1,1
            font_size: 20
        Label:
            id: beta2a_value
            pos_hint: {"center_x": 0.42, "center_y": 0.31}
            text: '0.003'
            markup: True
            color: 1,1,1
            font_size: 20
        Label:
            id: c2a_label
            pos_hint: {"center_x": 0.32, "center_y": 0.24}
            text: 'Current:'
            markup: True
            color: 1,1,1
            font_size: 20
        Label:
            id: c2a_value
            pos_hint: {"center_x": 0.42, "center_y": 0.24}
            text: '0.003'
            markup: True
            color: 1,1,1
            font_size: 20
        Label:
            id: v2a_label
            pos_hint: {"center_x": 0.32, "center_y": 0.17}
            text: 'Voltage:'
            markup: True
            color: 1,1,1
            font_size: 20
        Label:
            id: v2a_value
            pos_hint: {"center_x": 0.42, "center_y": 0.17}
            text: '0.003'
            markup: True
            color: 1,1,1
            font_size: 20   
            
        Label:
            pos_hint: {"center_x": 0.12, "center_y": 0.85}
            text: 'Channel 2B'
            markup: True
            color: 1,0,1
            font_size: 30
        Label:
            id: beta2b_label
            pos_hint: {"center_x": 0.07, "center_y": 0.78}
            text: 'Angle:'
            markup: True
            color: 1,1,1
            font_size: 20
        Label:
            id: beta2b_value
            pos_hint: {"center_x": 0.17, "center_y": 0.78}
            text: '0.003'
            markup: True
            color: 1,1,1
            font_size: 20
        Label:
            id: c2b_label
            pos_hint: {"center_x": 0.07, "center_y": 0.71}
            text: 'Current:'
            markup: True
            color: 1,1,1
            font_size: 20
        Label:
            id: c2b_value
            pos_hint: {"center_x": 0.17, "center_y": 0.71}
            text: '0.003'
            markup: True
            color: 1,1,1
            font_size: 20
        Label:
            id: v2b_label
            pos_hint: {"center_x": 0.07, "center_y": 0.64}
            text: 'Voltage:'
            markup: True
            color: 1,1,1
            font_size: 20
        Label:
            id: v2b_value
            pos_hint: {"center_x": 0.17, "center_y": 0.64}
            text: '0.003'
            markup: True
            color: 1,1,1
            font_size: 20    
            
        Label:
            pos_hint: {"center_x": 0.62, "center_y": 0.38}
            text: 'Channel 3A'
            markup: True
            color: 1,0,1
            font_size: 30
        Label:
            id: beta3a_label
            pos_hint: {"center_x": 0.57, "center_y": 0.31}
            text: 'Angle:'
            markup: True
            color: 1,1,1
            font_size: 20
        Label:
            id: beta3a_value
            pos_hint: {"center_x": 0.67, "center_y": 0.31}
            text: '0.003'
            markup: True
            color: 1,1,1
            font_size: 20   
        Label:
            id: c3a_label
            pos_hint: {"center_x": 0.57, "center_y": 0.24}
            text: 'Current:'
            markup: True
            color: 1,1,1
            font_size: 20
        Label:
            id: c3a_value
            pos_hint: {"center_x": 0.67, "center_y": 0.24}
            text: '0.003'
            markup: True
            color: 1,1,1
            font_size: 20
        Label:
            id: v3a_label
            pos_hint: {"center_x": 0.57, "center_y": 0.17}
            text: 'Voltage:'
            markup: True
            color: 1,1,1
            font_size: 20
        Label:
            id: v3a_value
            pos_hint: {"center_x": 0.67, "center_y": 0.17}
            text: '0.003'
            markup: True
            color: 1,1,1
            font_size: 20   
            
        Label:
            pos_hint: {"center_x": 0.87, "center_y": 0.85}
            text: 'Channel 3B'
            markup: True
            color: 1,0,1
            font_size: 30
        Label:
            id: beta3b_label
            pos_hint: {"center_x": 0.82, "center_y": 0.78}
            text: 'Angle:'
            markup: True
            color: 1,1,1
            font_size: 20
        Label:
            id: beta3b_value
            pos_hint: {"center_x": 0.92, "center_y": 0.78}
            text: '0.003'
            markup: True
            color: 1,1,1
            font_size: 20
        Label:
            id: c3b_label
            pos_hint: {"center_x": 0.82, "center_y": 0.71}
            text: 'Current:'
            markup: True
            color: 1,1,1
            font_size: 20
        Label:
            id: c3b_value
            pos_hint: {"center_x": 0.92, "center_y": 0.71}
            text: '0.003'
            markup: True
            color: 1,1,1
            font_size: 20
        Label:
            id: v3b_label
            pos_hint: {"center_x": 0.82, "center_y": 0.64}
            text: 'Voltage:'
            markup: True
            color: 1,1,1
            font_size: 20
        Label:
            id: v3b_value
            pos_hint: {"center_x": 0.92, "center_y": 0.64}
            text: '0.003'
            markup: True
            color: 1,1,1
            font_size: 20
            
        Label:
            pos_hint: {"center_x": 0.37, "center_y": 0.85}
            text: 'Channel 4A'
            markup: True
            color: 1,0,1
            font_size: 30
        Label:
            id: beta4a_label
            pos_hint: {"center_x": 0.32, "center_y": 0.78}
            text: 'Angle:'
            markup: True
            color: 1,1,1
            font_size: 20
        Label:
            id: beta4a_value
            pos_hint: {"center_x": 0.42, "center_y": 0.78}
            text: '0.003'
            markup: True
            color: 1,1,1
            font_size: 20
        Label:
            id: c4a_label
            pos_hint: {"center_x": 0.32, "center_y": 0.71}
            text: 'Current:'
            markup: True
            color: 1,1,1
            font_size: 20
        Label:
            id: c4a_value
            pos_hint: {"center_x": 0.42, "center_y": 0.71}
            text: '0.003'
            markup: True
            color: 1,1,1
            font_size: 20
        Label:
            id: v4a_label
            pos_hint: {"center_x": 0.32, "center_y": 0.64}
            text: 'Voltage:'
            markup: True
            color: 1,1,1
            font_size: 20
        Label:
            id: v4a_value
            pos_hint: {"center_x": 0.42, "center_y": 0.64}
            text: '0.003'
            markup: True
            color: 1,1,1
            font_size: 20
            
        Label:
            pos_hint: {"center_x": 0.12, "center_y": 0.38}
            text: 'Channel 4B'
            markup: True
            color: 1,0,1
            font_size: 30
        Label:
            id: beta4b_label
            pos_hint: {"center_x": 0.07, "center_y": 0.31}
            text: 'Angle:'
            markup: True
            color: 1,1,1
            font_size: 20
        Label:
            id: beta4b_value
            pos_hint: {"center_x": 0.17, "center_y": 0.31}
            text: '0.003'
            markup: True
            color: 1,1,1
            font_size: 20
        Label:
            id: c4b_label
            pos_hint: {"center_x": 0.07, "center_y": 0.24}
            text: 'Current:'
            markup: True
            color: 1,1,1
            font_size: 20
        Label:
            id: c4b_value
            pos_hint: {"center_x": 0.17, "center_y": 0.24}
            text: '0.003'
            markup: True
            color: 1,1,1
            font_size: 20
        Label:
            id: v4b_label
            pos_hint: {"center_x": 0.07, "center_y": 0.17}
            text: 'Voltage:'
            markup: True
            color: 1,1,1
            font_size: 20
        Label:
            id: v4b_value
            pos_hint: {"center_x": 0.17, "center_y": 0.17}
            text: '0.003'
            markup: True
            color: 1,1,1
            font_size: 20
        
<MimicScreen>:
    name: 'mimic'
    FloatLayout:
        id: mimicscreenlayout
        Image:
            source: './imgs/iss_photo1.jpg'
            allow_stretch: True
            keep_ratio: False
        Label:
            id: EVa_value
            pos_hint: {"center_x": 0.2, "center_y": 0.17}
            text: ''
            markup: True
            color: 0,0,0
            font_size: 30
        Button:
            size_hint: 0.2,0.1
            pos_hint: {"center_x": 0.12, "center_y": 0.9}
            text: 'EPS'
            font_size: 30
            on_release: root.manager.current = 'eps'
        Button:
            size_hint: 0.2,0.1
            pos_hint: {"center_x": 0.245, "center_y": 0.78}
            text: 'Crew'
            font_size: 30
            on_release: root.manager.current = 'crew'
        Button:
            size_hint: 0.2,0.1
            pos_hint: {"center_x": 0.85, "center_y": 0.78}
            text: 'Orbit'
            font_size: 30
            on_release: root.manager.current = 'orbit'
        Button:
            size_hint: 0.2,0.1
            pos_hint: {"center_x": 0.37, "center_y": 0.9}
            text: 'C&T'
            font_size: 30
            on_release: root.manager.current = 'ct'
        Button:
            size_hint: 0.2,0.1
            pos_hint: {"center_x": 0.62, "center_y": 0.9}
            text: 'TCS'
            font_size: 30
            on_release: root.manager.current = 'tcs'
        Button:
            size_hint: 0.2,0.1
            pos_hint: {"center_x": 0.87, "center_y": 0.9}
            text: 'GNC'
            font_size: 30
            on_release: root.manager.current = 'tcs'
        Label:
            id: differencelabel
            pos_hint: {"center_x": 0.15, "center_y": 0.22}
            text: 'Antenna dif'
            markup: True
            color: 1,0,1
            font_size: 30
        Label:
            id: difference
            pos_hint: {"center_x": 0.4, "center_y": 0.22}
            text: '0.00'
            markup: True
            color: 1,0,1
            font_size: 30
        Label:
            pos_hint: {"center_x": 0.6, "center_y": 0.78}
            text: 'ISS Information'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: velocity_label
            pos_hint: {"center_x": 0.45, "center_y": 0.7}
            text: 'Speed'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: velocity_value
            pos_hint: {"center_x": 0.75, "center_y": 0.7}
            text: '0.00'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: altitude_label
            pos_hint: {"center_x": 0.45, "center_y": 0.6}
            text: 'Altitude'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: altitude_value
            pos_hint: {"center_x": 0.75, "center_y": 0.6}
            text: '0.00'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: stationmass_label
            pos_hint: {"center_x": 0.45, "center_y": 0.5}
            text: 'Total Mass'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: stationmass_value
            pos_hint: {"center_x": 0.75, "center_y": 0.5}
            text: '0.00 kg'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: stationmode_label
            pos_hint: {"center_x": 0.45, "center_y": 0.4}
            text: 'Station Mode'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: stationmode_value
            pos_hint: {"center_x": 0.75, "center_y": 0.4}
            text: 'Standard'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: aoslabel
            pos_hint: {"center_x": 0.53, "center_y": 0.05}
            text: 'Signal Status:'
            markup: True
            color: 1,1,1
            font_size: 30
        Label:
            id: aosvalue
            pos_hint: {"center_x": 0.8, "center_y": 0.05}
            text: ' '
            markup: True
            color: 1,1,1
            font_size: 30
        Button:
            id: mimicstartbutton
            size_hint: 0.2,0.1
            pos_hint: {"x": 0.05, "y": 0.6}
            text: 'Transmit'
            disabled: False
            font_size: 30
            on_release: mimicstartbutton.text = 'Sending...'
            on_release: root.changeMimicBoolean(True)
            on_release: mimicstopbutton.disabled = False
            on_release: mimicstartbutton.disabled = True
        Button:
            id: mimicstopbutton
            size_hint: 0.2,0.1
            pos_hint: {"x": 0.05, "y": 0.45}
            text: 'Stop'
            disabled: True
            font_size: 30
            on_release: mimicstartbutton.text = 'Transmit'
            on_release: root.changeMimicBoolean(False)
            on_release: root.changeSwitchBoolean(False)
            on_release: mimicstopbutton.disabled = True
            on_release: mimicstartbutton.disabled = False
        Button:
            size_hint: 0.2,0.1
            pos_hint: {"Left": 1, "Bottom": 1}
            text: 'Return'
            font_size: 30
            on_release: root.changeMimicBoolean(False)
            on_release: root.changeSwitchBoolean(False)
            on_release: app.root.current = 'main'
           
<TriangleButton>:
    canvas.after:
        Color:
            rgba: self.triangle_color
        Triangle:
            points: self.p1 + self.p2 + self.p3
            
''')

if __name__ == '__main__':
    MainApp().run()

#runTouchApp(root_widget)
