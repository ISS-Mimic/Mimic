#!/usr/bin/python

from datetime import datetime, timedelta #used for time conversions and logging timestamps
import datetime as dtime #this is different from above for... reasons?
import os # used to remove database on program exit; also used for importing config.json
from subprocess import Popen #, PIPE, STDOUT #used to start/stop Javascript telemetry program and TDRS script and orbitmap
import time #used for time
import math #used for math
import glob #used to parse serial port names
import sqlite3 #used to access ISS telemetry database
import pytz #used for timezone conversion in orbit pass predictions
from bs4 import BeautifulSoup #used to parse webpages for data (EVA stats, ISS TLE)
import numpy as np
import ephem #used for TLE orbit information on orbit screen
import serial #used to send data over serial to arduino
import json # used for serial port config
from pyudev import Context, Devices, Monitor, MonitorObserver # for automatically detecting Arduinos
import argparse
import sys

# This is here because Kivy gets upset if you pass in your own non-Kivy args
CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), "config.json")
parser = argparse.ArgumentParser(description='ISS Mimic GUI. Arguments listed below are non-Kivy arguments.')
parser.add_argument(
        '--config', action='store_true',
        help='use config.json to manually specify serial ports to use',
        default=False)
args, kivy_args = parser.parse_known_args()
sys.argv[1:] = kivy_args
USE_CONFIG_JSON = args.config

from kivy.app import App
from kivy.lang import Builder
from kivy.network.urlrequest import UrlRequest #using this to request webpages
from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import ScreenManager, Screen, SwapTransition
from kivy.uix.popup import Popup
from kivy.uix.label import Label

import database_initialize # create and populate database script

""" Unused imports
import kivy
from kivy.core.window import Window
import threading #trying to send serial write to other thread
matplotlib for plotting day/night time
import matplotlib.pyplot as plt
from matplotlib import path
from mpl_toolkits.basemap import Basemap
"""

# Constants
SERIAL_SPEED = 9600

os.environ['KIVY_GL_BACKEND'] = 'gl' #need this to fix a kivy segfault that occurs with python3 for some reason

# Create Program Logs
mimiclog = open('/home/pi/Mimic/Pi/Logs/mimiclog.txt', 'w')

def logWrite(*args):
    mimiclog.write(str(datetime.utcnow()))
    mimiclog.write(' ')
    mimiclog.write(str(args[0]))
    mimiclog.write('\n')
    mimiclog.flush()

logWrite("Initialized Mimic Program Log")

#-------------------------Look for a connected arduino-----------------------------------

def remove_tty_device(name_to_remove):
    """ Removes tty device from list of serial ports. """
    global SERIAL_PORTS, OPEN_SERIAL_PORTS
    try:
        SERIAL_PORTS.remove(name_to_remove)
        idx_to_remove = -1
        for x in range(len(OPEN_SERIAL_PORTS)):
            if name_to_remove in str(OPEN_SERIAL_PORTS[x]):
                idx_to_remove = x
        if idx_to_remove != -1:
            del OPEN_SERIAL_PORTS[idx_to_remove]
            log_str = "Removed %s." % name_to_remove
            logWrite(log_str)
            print(log_str)
    except ValueError:
        # Not printing anything because it sometimes tries too many times and is irrelevant
        pass

def add_tty_device(name_to_add):
    """ Adds tty device to list of serial ports after it successfully opens. """
    global SERIAL_PORTS, OPEN_SERIAL_PORTS
    if name_to_add not in SERIAL_PORTS:
        try:
            SERIAL_PORTS.append(name_to_add)
            OPEN_SERIAL_PORTS.append(serial.Serial(SERIAL_PORTS[-1], SERIAL_SPEED, write_timeout=0, timeout=0))
            log_str = "Added and opened %s." % name_to_add
            logWrite(log_str)
            print(log_str)
        except IOError as e:
            # Not printing anything because sometimes it successfully opens soon after
            remove_tty_device(name_to_add) # don't leave it in the list if it didn't open

def detect_device_event(device):
    """ Callback for MonitorObserver to detect tty device and add or remove it. """
    if 'tty' in device.device_path:
        name = '/dev/' + (device.device_path).split('/')[-1:][0]
        if device.action == 'remove':
            remove_tty_device(name)
        if device.action == 'add':
            add_tty_device(name)

def is_arduino_id_vendor_string(text):
    """
    It's not ideal to have to include FTDI because that's somewhat
    generic, but if we want to use something like the Arduino Nano,
    that's what it shows up as. If it causes a problem, we can change
    it -- or the user can specify to use the config.json file instead.
    """
    if "Arduino" in text or "Adafruit" in text or "FTDI" in text:
        return True
    return False

def parse_tty_name(device, val):
    """
    Parses tty name from ID_VENDOR string.

    Example of device as a string:
    Device('/sys/devices/platform/scb/fd500000.pcie/pci0000:00/0000:00:00.0/0000:01:00.0/usb1/1-1/1-1.1/1-1.1.1/1-1.1.1:1.0/tty/ttyACM0')
    """
    if is_arduino_id_vendor_string(val):
        name = str(device).split('/')[-1:][0][:-2] # to get ttyACM0, etc.
        return '/dev/' + name
    logWrite("Skipping serial device:\n%s" % str(device))

def get_tty_dev_names(context):
    """ Checks ID_VENDOR string of tty devices to identify Arduinos. """
    names = []
    devices = context.list_devices(subsystem='tty')
    for d in devices:
        for k, v in d.items():
            if k is not None and k == 'ID_VENDOR':
                names.append(parse_tty_name(d, v))
    return names

def get_config_data():
    """ Get the JSON config data. """
    data = {}
    with open (CONFIG_FILE_PATH, 'r') as f:
        data = json.load(f)
    return data

def get_serial_ports(context, using_config_file=False):
    """ Gets the serial ports either from a config file or pyudev """
    serial_ports = []
    if using_config_file:
        data = get_config_data()
        serial_ports = data['arduino']['serial_ports']
    else:
        serial_ports = get_tty_dev_names(context)
    return serial_ports

def open_serial_ports(serial_ports):
    """ Open all the serial ports in the list. Used when the GUI is first opened. """
    global OPEN_SERIAL_PORTS
    try:
        for s in serial_ports:
            OPEN_SERIAL_PORTS.append(serial.Serial(s, SERIAL_SPEED, write_timeout=0, timeout=0))
    except (OSError, serial.SerialException) as e:
        if USE_CONFIG_JSON:
            print("\nNot all serial ports were detected. Check config.json for accuracy.\n\n%s" % e)
        raise Exception(e)

def serialWrite(*args):
    """ Writes to serial ports in list. """
    logWrite("Function call - serial write: " + str(*args))
    for s in OPEN_SERIAL_PORTS:
        try:
            s.write(str.encode(*args))
        except (OSError, serial.SerialException) as e:
            logWrite(e)

context = Context()
if not USE_CONFIG_JSON:
    MONITOR = Monitor.from_netlink(context)
    TTY_OBSERVER = MonitorObserver(MONITOR, callback=detect_device_event, name='monitor-observer')
    TTY_OBSERVER.daemon = False
SERIAL_PORTS = get_serial_ports(context, USE_CONFIG_JSON)
OPEN_SERIAL_PORTS = []
open_serial_ports(SERIAL_PORTS)
log_str = "Serial ports opened: %s" % str(SERIAL_PORTS)
logWrite(log_str)
print(log_str)
if not USE_CONFIG_JSON:
    TTY_OBSERVER.start()
    log_str = "Started monitoring serial ports."
    print(log_str)
    logWrite(log_str)

#-------------------------TDRS Checking Database-----------------------------------------
TDRSconn = sqlite3.connect('/dev/shm/tdrs.db')
TDRSconn.isolation_level = None
TDRScursor = TDRSconn.cursor()
conn = sqlite3.connect('/dev/shm/iss_telemetry.db')
conn.isolation_level = None
c = conn.cursor()

def staleTelemetry():
    c.execute("UPDATE telemetry SET Value = 'Unsubscribed' where Label = 'Lightstreamer'")
#----------------------------------Variables---------------------------------------------
LS_Subscription = False
isslocationsuccess = False
testfactor = -1
crew_mention= False
mimicbutton = False
fakeorbitboolean = False
demoboolean = False
switchtofake = False
manualcontrol = False
startup = True
isscrew = 0
val = ""
tdrs1 = 0
tdrs2 = 0
tdrs_timestamp = 0
lastsignal = 0
testvalue = 0
obtained_EVA_crew = False
unixconvert = time.gmtime(time.time())
EVAstartTime = float(unixconvert[7])*24+unixconvert[3]+float(unixconvert[4])/60+float(unixconvert[5])/3600
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
oldtdrs = "n/a"
runningDemo = False
Disco = False
logged = False
mt_speed = 0.00
#-----------EPS Variables----------------------
EPSstorageindex = 0
channel1A_voltage = [154.1, 154.1, 154.1, 154.1, 154.1, 154.1, 154.1, 154.1, 154.1, 154.1]
channel1B_voltage = [154.1, 154.1, 154.1, 154.1, 154.1, 154.1, 154.1, 154.1, 154.1, 154.1]
channel2A_voltage = [154.1, 154.1, 154.1, 154.1, 154.1, 154.1, 154.1, 154.1, 154.1, 154.1]
channel2B_voltage = [154.1, 154.1, 154.1, 154.1, 154.1, 154.1, 154.1, 154.1, 154.1, 154.1]
channel3A_voltage = [154.1, 154.1, 154.1, 154.1, 154.1, 154.1, 154.1, 154.1, 154.1, 154.1]
channel3B_voltage = [154.1, 154.1, 154.1, 154.1, 154.1, 154.1, 154.1, 154.1, 154.1, 154.1]
channel4A_voltage = [154.1, 154.1, 154.1, 154.1, 154.1, 154.1, 154.1, 154.1, 154.1, 154.1]
channel4B_voltage = [154.1, 154.1, 154.1, 154.1, 154.1, 154.1, 154.1, 154.1, 154.1, 154.1]
sizeX = 0.00
sizeY = 0.00
psarj2 = 1.0
ssarj2 = 1.0
new_x = 0
new_y = 0
new_x2 = 0
new_y2 = 0
aos = 0.00
los = 0.00
sgant_elevation = 0.00
sgant_xelevation = 0.00
sgant_elevation_old = -110.00
seconds2 = 260
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
US_EVAinProgress = False
leak_hold = False
firstcrossing = True
oldAirlockPump = 0.00
position_x = 0.00
position_y = 0.00
position_z = 0.00
velocity_x = 0.00
velocity_y = 0.00
velocity_z = 0.00
velocity = 0.00
altitude = 0.00
mass = 0.00
crewlockpres = 758
EVA_activities = False
repress = False
depress = False
seconds = 0
minutes = 0
hours = 0
leak_hold = False
EV1 = ""
EV2 = ""
numEVAs1 = ""
EVAtime_hours1 = ""
EVAtime_minutes1 = ""
numEVAs2 = ""
EVAtime_hours2 = ""
EVAtime_minutes2 = ""
holdstartTime = float(unixconvert[7])*24+unixconvert[3]+float(unixconvert[4])/60+float(unixconvert[5])/3600
eva = False
standby = False
prebreath1 = False
prebreath2 = False
depress1 = False
depress2 = False
leakhold = False
repress = False
ISS_TLE_Acquired = False
stationmode = 0.00
tdrs = ""
EVA_picture_urls = []
urlindex = 0
module = ""
internet = False
old_mt_timestamp = 0.00
old_mt_position = 0.00

class MainScreen(Screen):
    def changeManualControlBoolean(self, *args):
        global manualcontrol
        manualcontrol = args[0]

    def killproc(*args):
        global p,p2
        if not USE_CONFIG_JSON:
            TTY_OBSERVER.stop()
            log_str = "Stopped monitoring serial ports."
            logWrite(log_str)
            print(log_str)
        try:
            p.kill()
            p2.kill()
        except Exception:
            pass
        os.system('rm /dev/shm/iss_telemetry.db') #delete sqlite database on exit, db is recreated each time to avoid concurrency issues
        os.system('rm /dev/shm/tdrs.db') #delete sqlite database on exit, db is recreated each time to avoid concurrency issues
        staleTelemetry()
        logWrite("Successfully stopped ISS telemetry javascript and removed database")

class ManualControlScreen(Screen):
    def on_pre_enter(self): #call the callback funcion when activating this screen, to update all angles
        self.callback()

    def callback(self):
        global psarjmc,ssarjmc,ptrrjmc,strrjmc,beta1amc,beta1bmc,beta2amc,beta2bmc,beta3amc,beta3bmc,beta4amc,beta4bmc
        self.ids.Beta4B_Button.text = "4B\n" + str(math.trunc(beta4bmc))
        self.ids.Beta4A_Button.text = "4A\n" + str(math.trunc(beta4amc))
        self.ids.Beta3B_Button.text = "3B\n" + str(math.trunc(beta3bmc))
        self.ids.Beta3A_Button.text = "3A\n" + str(math.trunc(beta3amc))
        self.ids.Beta2B_Button.text = "2B\n" + str(math.trunc(beta2bmc))
        self.ids.Beta2A_Button.text = "2A\n" + str(math.trunc(beta2amc))
        self.ids.Beta1B_Button.text = "1B\n" + str(math.trunc(beta1bmc))
        self.ids.Beta1A_Button.text = "1A\n" + str(math.trunc(beta1amc))
        self.ids.PSARJ_Button.text = "PSARJ " + str(math.trunc(psarjmc))
        self.ids.SSARJ_Button.text = "SSARJ " + str(math.trunc(ssarjmc))
        self.ids.PTRRJ_Button.text = "PTRRJ\n" + str(math.trunc(ptrrjmc))
        self.ids.STRRJ_Button.text = "STRRJ\n" + str(math.trunc(strrjmc))

    def zeroJoints(self):
        global psarjmc,ssarjmc,ptrrjmc,strrjmc,beta1amc,beta1bmc,beta2amc,beta2bmc,beta3amc,beta3bmc,beta4amc,beta4bmc
        serialWrite("NULLIFY=1 ")
        c.execute("UPDATE telemetry SET Value = '0' WHERE Label = 'beta1a'")
        beta1amc = 0.00
        c.execute("UPDATE telemetry SET Value = '0' WHERE Label = 'beta1b'")
        beta1bmc = 0.00
        c.execute("UPDATE telemetry SET Value = '0' WHERE Label = 'beta2a'")
        beta2amc = 0.00
        c.execute("UPDATE telemetry SET Value = '0' WHERE Label = 'beta2b'")
        beta2bmc = 0.00
        c.execute("UPDATE telemetry SET Value = '0' WHERE Label = 'beta3a'")
        beta3amc = 0.00
        c.execute("UPDATE telemetry SET Value = '0' WHERE Label = 'beta3b'")
        beta3bmc = 0.00
        c.execute("UPDATE telemetry SET Value = '0' WHERE Label = 'beta4a'")
        beta4amc = 0.00
        c.execute("UPDATE telemetry SET Value = '0' WHERE Label = 'beta4b'")
        beta4bmc = 0.00
        c.execute("UPDATE telemetry SET Value = '0' WHERE Label = 'psarj'")
        psarjmc = 0.00
        c.execute("UPDATE telemetry SET Value = '0' WHERE Label = 'ssarj'")
        ssarjmc = 0.00
        self.callback()

    def setActive(self, *args):
        global Beta4Bcontrol, Beta3Bcontrol, Beta2Bcontrol, Beta1Bcontrol, Beta4Acontrol, Beta3Acontrol, Beta2Acontrol, Beta1Acontrol, PSARJcontrol, SSARJcontrol, PTRRJcontrol, STRRJcontrol
        if str(args[0])=="Beta4B":
            Beta4Bcontrol = True
            Beta4Acontrol = False
            Beta3Bcontrol = False
            Beta3Acontrol = False
            Beta2Bcontrol = False
            Beta2Acontrol = False
            Beta1Bcontrol = False
            Beta1Acontrol = False
            PSARJcontrol = False
            SSARJcontrol = False
            PTRRJcontrol = False
            STRRJcontrol = False
            self.ids.Beta4B_Button.background_color = (0, 0, 1, 1)
            self.ids.Beta4A_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta3B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta3A_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta2B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta2A_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta1B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta1A_Button.background_color = (1, 1, 1, 1)
            self.ids.PSARJ_Button.background_color = (1, 1, 1, 1)
            self.ids.SSARJ_Button.background_color = (1, 1, 1, 1)
            self.ids.PTRRJ_Button.background_color = (1, 1, 1, 1)
            self.ids.STRRJ_Button.background_color = (1, 1, 1, 1)
        if str(args[0])=="Beta3B":
            Beta3Bcontrol = True
            Beta4Bcontrol = False
            Beta4Acontrol = False
            Beta3Acontrol = False
            Beta2Bcontrol = False
            Beta2Acontrol = False
            Beta1Bcontrol = False
            Beta1Acontrol = False
            PSARJcontrol = False
            SSARJcontrol = False
            PTRRJcontrol = False
            STRRJcontrol = False
            self.ids.Beta4B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta4A_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta3B_Button.background_color = (0, 0, 1, 1)
            self.ids.Beta3A_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta2B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta2A_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta1B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta1A_Button.background_color = (1, 1, 1, 1)
            self.ids.PSARJ_Button.background_color = (1, 1, 1, 1)
            self.ids.SSARJ_Button.background_color = (1, 1, 1, 1)
            self.ids.PTRRJ_Button.background_color = (1, 1, 1, 1)
            self.ids.STRRJ_Button.background_color = (1, 1, 1, 1)
        if str(args[0])=="Beta2B":
            Beta2Bcontrol = True
            Beta4Bcontrol = False
            Beta4Acontrol = False
            Beta3Bcontrol = False
            Beta3Acontrol = False
            Beta2Acontrol = False
            Beta1Bcontrol = False
            Beta1Acontrol = False
            PSARJcontrol = False
            SSARJcontrol = False
            PTRRJcontrol = False
            STRRJcontrol = False
            self.ids.Beta4B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta4A_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta3B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta3A_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta2B_Button.background_color = (0, 0, 1, 1)
            self.ids.Beta2A_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta1B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta1A_Button.background_color = (1, 1, 1, 1)
            self.ids.PSARJ_Button.background_color = (1, 1, 1, 1)
            self.ids.SSARJ_Button.background_color = (1, 1, 1, 1)
            self.ids.PTRRJ_Button.background_color = (1, 1, 1, 1)
            self.ids.STRRJ_Button.background_color = (1, 1, 1, 1)
        if str(args[0])=="Beta1B":
            Beta1Bcontrol = True
            Beta4Bcontrol = False
            Beta4Acontrol = False
            Beta3Bcontrol = False
            Beta3Acontrol = False
            Beta2Bcontrol = False
            Beta2Acontrol = False
            Beta1Acontrol = False
            PSARJcontrol = False
            SSARJcontrol = False
            PTRRJcontrol = False
            STRRJcontrol = False
            self.ids.Beta4B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta4A_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta3B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta3A_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta2B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta2A_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta1B_Button.background_color = (0, 0, 1, 1)
            self.ids.Beta1A_Button.background_color = (1, 1, 1, 1)
            self.ids.PSARJ_Button.background_color = (1, 1, 1, 1)
            self.ids.SSARJ_Button.background_color = (1, 1, 1, 1)
            self.ids.PTRRJ_Button.background_color = (1, 1, 1, 1)
            self.ids.STRRJ_Button.background_color = (1, 1, 1, 1)
        if str(args[0])=="Beta4A":
            Beta4Acontrol = True
            Beta4Bcontrol = False
            Beta3Bcontrol = False
            Beta3Acontrol = False
            Beta2Bcontrol = False
            Beta2Acontrol = False
            Beta1Bcontrol = False
            Beta1Acontrol = False
            PSARJcontrol = False
            SSARJcontrol = False
            PTRRJcontrol = False
            STRRJcontrol = False
            self.ids.Beta4B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta4A_Button.background_color = (0, 0, 1, 1)
            self.ids.Beta3B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta3A_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta2B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta2A_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta1B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta1A_Button.background_color = (1, 1, 1, 1)
            self.ids.PSARJ_Button.background_color = (1, 1, 1, 1)
            self.ids.SSARJ_Button.background_color = (1, 1, 1, 1)
            self.ids.PTRRJ_Button.background_color = (1, 1, 1, 1)
            self.ids.STRRJ_Button.background_color = (1, 1, 1, 1)
        if str(args[0])=="Beta3A":
            Beta3Acontrol = True
            Beta4Bcontrol = False
            Beta4Acontrol = False
            Beta3Bcontrol = False
            Beta2Bcontrol = False
            Beta2Acontrol = False
            Beta1Bcontrol = False
            Beta1Acontrol = False
            PSARJcontrol = False
            SSARJcontrol = False
            PTRRJcontrol = False
            STRRJcontrol = False
            self.ids.Beta4B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta4A_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta3B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta3A_Button.background_color = (0, 0, 1, 1)
            self.ids.Beta2B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta2A_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta1B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta1A_Button.background_color = (1, 1, 1, 1)
            self.ids.PSARJ_Button.background_color = (1, 1, 1, 1)
            self.ids.SSARJ_Button.background_color = (1, 1, 1, 1)
            self.ids.PTRRJ_Button.background_color = (1, 1, 1, 1)
            self.ids.STRRJ_Button.background_color = (1, 1, 1, 1)
        if str(args[0])=="Beta2A":
            Beta2Acontrol = True
            Beta4Bcontrol = False
            Beta4Acontrol = False
            Beta3Bcontrol = False
            Beta3Acontrol = False
            Beta2Bcontrol = False
            Beta1Bcontrol = False
            Beta1Acontrol = False
            PSARJcontrol = False
            SSARJcontrol = False
            PTRRJcontrol = False
            STRRJcontrol = False
            self.ids.Beta4B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta4A_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta3B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta3A_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta2B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta2A_Button.background_color = (0, 0, 1, 1)
            self.ids.Beta1B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta1A_Button.background_color = (1, 1, 1, 1)
            self.ids.PSARJ_Button.background_color = (1, 1, 1, 1)
            self.ids.SSARJ_Button.background_color = (1, 1, 1, 1)
            self.ids.PTRRJ_Button.background_color = (1, 1, 1, 1)
            self.ids.STRRJ_Button.background_color = (1, 1, 1, 1)
        if str(args[0])=="Beta1A":
            Beta1Acontrol = True
            Beta4Bcontrol = False
            Beta4Acontrol = False
            Beta3Bcontrol = False
            Beta3Acontrol = False
            Beta2Bcontrol = False
            Beta2Acontrol = False
            Beta1Bcontrol = False
            PSARJcontrol = False
            SSARJcontrol = False
            PTRRJcontrol = False
            STRRJcontrol = False
            self.ids.Beta4B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta4A_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta3B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta3A_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta2B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta2A_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta1B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta1A_Button.background_color = (0, 0, 1, 1)
            self.ids.PSARJ_Button.background_color = (1, 1, 1, 1)
            self.ids.SSARJ_Button.background_color = (1, 1, 1, 1)
            self.ids.PTRRJ_Button.background_color = (1, 1, 1, 1)
            self.ids.STRRJ_Button.background_color = (1, 1, 1, 1)
        if str(args[0])=="PTRRJ":
            PTRRJcontrol = True
            Beta4Bcontrol = False
            Beta4Acontrol = False
            Beta3Bcontrol = False
            Beta3Acontrol = False
            Beta2Bcontrol = False
            Beta2Acontrol = False
            Beta1Bcontrol = False
            Beta1Acontrol = False
            PSARJcontrol = False
            SSARJcontrol = False
            STRRJcontrol = False
            self.ids.Beta4B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta4A_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta3B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta3A_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta2B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta2A_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta1B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta1A_Button.background_color = (1, 1, 1, 1)
            self.ids.PSARJ_Button.background_color = (1, 1, 1, 1)
            self.ids.SSARJ_Button.background_color = (1, 1, 1, 1)
            self.ids.PTRRJ_Button.background_color = (0, 0, 1, 1)
            self.ids.STRRJ_Button.background_color = (1, 1, 1, 1)
        if str(args[0])=="STRRJ":
            STRRJcontrol = True
            Beta4Bcontrol = False
            Beta4Acontrol = False
            Beta3Bcontrol = False
            Beta3Acontrol = False
            Beta2Bcontrol = False
            Beta2Acontrol = False
            Beta1Bcontrol = False
            Beta1Acontrol = False
            PSARJcontrol = False
            SSARJcontrol = False
            PTRRJcontrol = False
            self.ids.Beta4B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta4A_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta3B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta3A_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta2B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta2A_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta1B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta1A_Button.background_color = (1, 1, 1, 1)
            self.ids.PSARJ_Button.background_color = (1, 1, 1, 1)
            self.ids.SSARJ_Button.background_color = (1, 1, 1, 1)
            self.ids.PTRRJ_Button.background_color = (1, 1, 1, 1)
            self.ids.STRRJ_Button.background_color = (0, 0, 1, 1)
        if str(args[0])=="PSARJ":
            PSARJcontrol = True
            Beta4Bcontrol = False
            Beta4Acontrol = False
            Beta3Bcontrol = False
            Beta3Acontrol = False
            Beta2Bcontrol = False
            Beta2Acontrol = False
            Beta1Bcontrol = False
            Beta1Acontrol = False
            SSARJcontrol = False
            PTRRJcontrol = False
            STRRJcontrol = False
            self.ids.Beta4B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta4A_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta3B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta3A_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta2B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta2A_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta1B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta1A_Button.background_color = (1, 1, 1, 1)
            self.ids.PSARJ_Button.background_color = (0, 0, 1, 1)
            self.ids.SSARJ_Button.background_color = (1, 1, 1, 1)
            self.ids.PTRRJ_Button.background_color = (1, 1, 1, 1)
            self.ids.STRRJ_Button.background_color = (1, 1, 1, 1)
        if str(args[0])=="SSARJ":
            SSARJcontrol = True
            Beta4Bcontrol = False
            Beta4Acontrol = False
            Beta3Bcontrol = False
            Beta3Acontrol = False
            Beta2Bcontrol = False
            Beta2Acontrol = False
            Beta1Bcontrol = False
            Beta1Acontrol = False
            PSARJcontrol = False
            PTRRJcontrol = False
            STRRJcontrol = False
            self.ids.Beta4B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta4A_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta3B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta3A_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta2B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta2A_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta1B_Button.background_color = (1, 1, 1, 1)
            self.ids.Beta1A_Button.background_color = (1, 1, 1, 1)
            self.ids.PSARJ_Button.background_color = (1, 1, 1, 1)
            self.ids.SSARJ_Button.background_color = (0, 0, 1, 1)
            self.ids.PTRRJ_Button.background_color = (1, 1, 1, 1)
            self.ids.STRRJ_Button.background_color = (1, 1, 1, 1)

    def incrementActive(self, *args):
        global Beta4Bcontrol, Beta3Bcontrol, Beta2Bcontrol, Beta1Bcontrol, Beta4Acontrol, Beta3Acontrol, Beta2Acontrol, Beta1Acontrol, PSARJcontrol, SSARJcontrol, PTRRJcontrol, STRRJcontrol

        if Beta4Bcontrol:
            self.incrementBeta4B(float(args[0]))
        if Beta3Bcontrol:
            self.incrementBeta3B(float(args[0]))
        if Beta2Bcontrol:
            self.incrementBeta2B(float(args[0]))
        if Beta1Bcontrol:
            self.incrementBeta1B(float(args[0]))
        if Beta4Acontrol:
            self.incrementBeta4A(float(args[0]))
        if Beta3Acontrol:
            self.incrementBeta3A(float(args[0]))
        if Beta2Acontrol:
            self.incrementBeta2A(float(args[0]))
        if Beta1Acontrol:
            self.incrementBeta1A(float(args[0]))
        if PTRRJcontrol:
            self.incrementPTRRJ(float(args[0]))
        if STRRJcontrol:
            self.incrementSTRRJ(float(args[0]))
        if PSARJcontrol:
            self.incrementPSARJ(float(args[0]))
        if SSARJcontrol:
            self.incrementSSARJ(float(args[0]))
        self.callback()

    def incrementPSARJ(self, *args):
        global psarjmc
        psarjmc += args[0]
        serialWrite("PSARJ=" + str(psarjmc) + " ")
        c.execute("UPDATE telemetry SET Value = ? WHERE Label = 'psarj'",(psarjmc,))
        self.ids.statusbar.text = "PSARJ Value Sent: " + str(psarjmc)

    def incrementSSARJ(self, *args):
        global ssarjmc
        ssarjmc += args[0]
        serialWrite("SSARJ=" + str(ssarjmc) + " ")
        c.execute("UPDATE telemetry SET Value = ? WHERE Label = 'ssarj'",(ssarjmc,))
        self.ids.statusbar.text = "SSARJ Value Sent: " + str(ssarjmc)

    def incrementPTRRJ(self, *args):
        global ptrrjmc
        ptrrjmc += args[0]
        serialWrite("PTRRJ=" + str(ptrrjmc) + " ")
        c.execute("UPDATE telemetry  SET Value = ? WHERE Label = 'ptrrj'",(ptrrjmc,))
        self.ids.statusbar.text = "PTRRJ Value Sent: " + str(ptrrjmc)

    def incrementSTRRJ(self, *args):
        global strrjmc
        strrjmc += args[0]
        serialWrite("STRRJ=" + str(strrjmc) + " ")
        c.execute("UPDATE telemetry SET Value = ? WHERE Label = 'strrj'",(strrjmc,))
        self.ids.statusbar.text = "STRRJ Value Sent: " + str(strrjmc)

    def incrementBeta1B(self, *args):
        global beta1bmc
        beta1bmc += args[0]
        serialWrite("B1B=" + str(beta1bmc) + " ")
        c.execute("UPDATE telemetry SET Value = ? WHERE Label = 'beta1b'",(beta1bmc,))
        self.ids.statusbar.text = "Beta1B Value Sent: " + str(beta1bmc)

    def incrementBeta1A(self, *args):
        global beta1amc
        beta1amc += args[0]
        serialWrite("B1A=" + str(beta1amc) + " ")
        c.execute("UPDATE telemetry SET Value = ? WHERE Label = 'beta1a'",(beta1amc,))
        self.ids.statusbar.text = "Beta1A Value Sent: " + str(beta1amc)

    def incrementBeta2B(self, *args):
        global beta2bmc
        beta2bmc += args[0]
        serialWrite("B2B=" + str(beta2bmc) + " ")
        c.execute("UPDATE telemetry SET Value = ? WHERE Label = 'beta2b'",(beta2bmc,))
        self.ids.statusbar.text = "Beta2B Value Sent: " + str(beta2bmc)

    def incrementBeta2A(self, *args):
        global beta2amc
        beta2amc += args[0]
        serialWrite("B2A=" + str(beta2amc) + " ")
        c.execute("UPDATE telemetry SET Value = ? WHERE Label = 'beta2a'",(beta2amc,))
        self.ids.statusbar.text = "Beta2A Value Sent: " + str(beta2amc)

    def incrementBeta3B(self, *args):
        global beta3bmc
        beta3bmc += args[0]
        serialWrite("B3B=" + str(beta3bmc) + " ")
        c.execute("UPDATE telemetry SET Value = ? WHERE Label = 'beta3b'",(beta3bmc,))
        self.ids.statusbar.text = "Beta3B Value Sent: " + str(beta3bmc)

    def incrementBeta3A(self, *args):
        global beta3amc
        beta3amc += args[0]
        serialWrite("B3A=" + str(beta3amc) + " ")
        c.execute("UPDATE telemetry SET Value = ? WHERE Label = 'beta3a'",(beta3amc,))
        self.ids.statusbar.text = "Beta3A Value Sent: " + str(beta3amc)

    def incrementBeta4B(self, *args):
        global beta4bmc
        beta4bmc += args[0]
        serialWrite("B4B=" + str(beta4bmc) + " ")
        c.execute("UPDATE telemetry SET Value = ? WHERE Label = 'beta4b'",(beta4bmc,))
        self.ids.statusbar.text = "Beta4B Value Sent: " + str(beta4bmc)

    def incrementBeta4A(self, *args):
        global beta4amc
        beta4amc += args[0]
        serialWrite("B4A=" + str(beta4amc) + " ")
        c.execute("UPDATE telemetry SET Value = ? WHERE Label = 'beta4a'",(beta4amc,))
        self.ids.statusbar.text = "Beta4A Value Sent: " + str(beta4amc)

    def changeBoolean(self, *args):
        global manualcontrol
        manualcontrol = args[0]

    def sendActive(self, *args):
        if Beta4Bcontrol:
            self.sendBeta4B(float(args[0]))
        if Beta3Bcontrol:
            self.sendBeta3B(float(args[0]))
        if Beta2Bcontrol:
            self.sendBeta2B(float(args[0]))
        if Beta1Bcontrol:
            self.sendBeta1B(float(args[0]))
        if Beta4Acontrol:
            self.sendBeta4A(float(args[0]))
        if Beta3Acontrol:
            self.sendBeta3A(float(args[0]))
        if Beta2Acontrol:
            self.sendBeta2A(float(args[0]))
        if Beta1Acontrol:
            self.sendBeta1A(float(args[0]))
        if PTRRJcontrol:
            self.sendPTRRJ(float(args[0]))
        if STRRJcontrol:
            self.sendSTRRJ(float(args[0]))
        if PSARJcontrol:
            self.sendPSARJ(float(args[0]))
        if SSARJcontrol:
            self.sendSSARJ(float(args[0]))

    def sendPSARJ(self, *args):
        global psarjmc
        psarjmc = args[0]
        serialWrite("PSARJ=" + str(args[0]) + " ")
        c.execute("UPDATE telemetry SET Value = ? WHERE Label = 'psarj'",(args[0],))
        self.ids.statusbar.text = "PSARJ Value Sent: " + str(args[0])

    def sendSSARJ(self, *args):
        global ssarjmc
        ssarjmc = args[0]
        serialWrite("SSARJ=" + str(args[0]) + " ")
        c.execute("UPDATE telemetry SET Value = ? WHERE Label = 'ssarj'",(args[0],))
        self.ids.statusbar.text = "SSARJ Value Sent: " + str(args[0])

    def sendPTRRJ(self, *args):
        global ptrrjmc
        ptrrjmc = args[0]
        serialWrite("PTRRJ=" + str(args[0]) + " ")
        c.execute("UPDATE telemetry  SET Value = ? WHERE Label = 'ptrrj'",(args[0],))
        self.ids.statusbar.text = "PTRRJ Value Sent: " + str(args[0])

    def sendSTRRJ(self, *args):
        global strrjmc
        strrjmc = args[0]
        serialWrite("STRRJ=" + str(args[0]) + " ")
        c.execute("UPDATE telemetry SET Value = ? WHERE Label = 'strrj'",(args[0],))
        self.ids.statusbar.text = "STRRJ Value Sent: " + str(args[0])

    def sendBeta1B(self, *args):
        global beta1bmc
        beta1bmc = args[0]
        serialWrite("B1B=" + str(args[0]) + " ")
        c.execute("UPDATE telemetry SET Value = ? WHERE Label = 'beta1b'",(args[0],))
        self.ids.statusbar.text = "Beta1B Value Sent: " + str(args[0])

    def sendBeta1A(self, *args):
        global beta1amc
        beta1amc = args[0]
        serialWrite("B1A=" + str(args[0]) + " ")
        c.execute("UPDATE telemetry SET Value = ? WHERE Label = 'beta1a'",(args[0],))
        self.ids.statusbar.text = "Beta1A Value Sent: " + str(args[0])

    def sendBeta2B(self, *args):
        global beta2bmc
        beta2bmc = args[0]
        serialWrite("B2B=" + str(args[0]) + " ")
        c.execute("UPDATE telemetry SET Value = ? WHERE Label = 'beta2b'",(args[0],))
        self.ids.statusbar.text = "Beta2B Value Sent: " + str(args[0])

    def sendBeta2A(self, *args):
        global beta2amc
        beta2amc = args[0]
        serialWrite("B2A=" + str(args[0]) + " ")
        c.execute("UPDATE telemetry SET Value = ? WHERE Label = 'beta2a'",(args[0],))
        self.ids.statusbar.text = "Beta2A Value Sent: " + str(args[0])

    def sendBeta3B(self, *args):
        global beta3bmc
        beta3bmc = args[0]
        serialWrite("B3B=" + str(args[0]) + " ")
        c.execute("UPDATE telemetry SET Value = ? WHERE Label = 'beta3b'",(args[0],))
        self.ids.statusbar.text = "Beta3B Value Sent: " + str(args[0])

    def sendBeta3A(self, *args):
        global beta3amc
        beta3amc = args[0]
        serialWrite("B3A=" + str(args[0]) + " ")
        c.execute("UPDATE telemetry SET Value = ? WHERE Label = 'beta3a'",(args[0],))
        self.ids.statusbar.text = "Beta3A Value Sent: " + str(args[0])

    def sendBeta4B(self, *args):
        global beta4bmc
        beta4bmc = args[0]
        serialWrite("B4B=" + str(args[0]) + " ")
        c.execute("UPDATE telemetry SET Value = ? WHERE Label = 'beta4b'",(args[0],))
        self.ids.statusbar.text = "Beta4B Value Sent: " + str(args[0])

    def sendBeta4A(self, *args):
        global beta4amc
        beta4amc = args[0]
        serialWrite("B4A=" + str(args[0]) + " ")
        c.execute("UPDATE telemetry SET Value = ? WHERE Label = 'beta4a'",(args[0],))
        self.ids.statusbar.text = "Beta4A Value Sent: " + str(args[0])

    def send0(self, *args):
        global psarjmc,ssarjmc,ptrrjmc,strrjmc,beta1amc,beta1bmc,beta2amc,beta2bmc,beta3amc,beta3bmc,beta4amc,beta4bmc
        c.execute("UPDATE telemetry SET Value = '0' WHERE Label = 'beta1a'")
        c.execute("UPDATE telemetry SET Value = '0' WHERE Label = 'beta1b'")
        c.execute("UPDATE telemetry SET Value = '0' WHERE Label = 'beta2a'")
        c.execute("UPDATE telemetry SET Value = '0' WHERE Label = 'beta2b'")
        c.execute("UPDATE telemetry SET Value = '0' WHERE Label = 'beta3a'")
        c.execute("UPDATE telemetry SET Value = '0' WHERE Label = 'beta3b'")
        c.execute("UPDATE telemetry SET Value = '0' WHERE Label = 'beta4a'")
        c.execute("UPDATE telemetry SET Value = '0' WHERE Label = 'beta4b'")
        c.execute("UPDATE telemetry SET Value = '0' WHERE Label = 'psarj'")
        c.execute("UPDATE telemetry SET Value = '0' WHERE Label = 'ssarj'")
        c.execute("UPDATE telemetry SET Value = '0' WHERE Label = 'ptrrj'")
        c.execute("UPDATE telemetry SET Value = '0' WHERE Label = 'strrj'")
        strrjmc = 0
        ptrrjmc = 0
        ssarjmc = 0
        psarjmc = 0
        beta1bmc = 0
        beta1amc = 0
        beta2bmc = 0
        beta2amc = 0
        beta3bmc = 0
        beta3amc = 0
        beta4bmc = 0
        beta4amc = 0
        self.ids.statusbar.text = "0 sent to all"
        serialWrite("B1A=0 ")
        serialWrite("B1B=0 ")
        serialWrite("B2A=0 ")
        serialWrite("B2B=0 ")
        serialWrite("B3A=0 ")
        serialWrite("B3B=0 ")
        serialWrite("B4A=0 ")
        serialWrite("B4B=0 ")
        serialWrite("PSARJ=0 ")
        serialWrite("SSARJ=0 ")
        serialWrite("PTRRJ=0 ")
        serialWrite("STRRJ=0 ")

    def send90(self, *args):
        global psarjmc,ssarjmc,ptrrjmc,strrjmc,beta1amc,beta1bmc,beta2amc,beta2bmc,beta3amc,beta3bmc,beta4amc,beta4bmc
        c.execute("UPDATE telemetry SET Value = '90' WHERE Label = 'beta1a'")
        c.execute("UPDATE telemetry SET Value = '90' WHERE Label = 'beta1b'")
        c.execute("UPDATE telemetry SET Value = '90' WHERE Label = 'beta2a'")
        c.execute("UPDATE telemetry SET Value = '90' WHERE Label = 'beta2b'")
        c.execute("UPDATE telemetry SET Value = '90' WHERE Label = 'beta3a'")
        c.execute("UPDATE telemetry SET Value = '90' WHERE Label = 'beta3b'")
        c.execute("UPDATE telemetry SET Value = '90' WHERE Label = 'beta4a'")
        c.execute("UPDATE telemetry SET Value = '90' WHERE Label = 'beta4b'")
        c.execute("UPDATE telemetry SET Value = '90' WHERE Label = 'psarj'")
        c.execute("UPDATE telemetry SET Value = '90' WHERE Label = 'ssarj'")
        c.execute("UPDATE telemetry SET Value = '90' WHERE Label = 'ptrrj'")
        c.execute("UPDATE telemetry SET Value = '90' WHERE Label = 'strrj'")
        strrjmc = 90
        ptrrjmc = 90
        ssarjmc = 90
        psarjmc = 90
        beta1bmc = 90
        beta1amc = 90
        beta2bmc = 90
        beta2amc = 90
        beta3bmc = 90
        beta3amc = 90
        beta4bmc = 90
        beta4amc = 90
        self.ids.statusbar.text = "90 sent to all"
        serialWrite("B1A=90 ")
        serialWrite("B1B=90 ")
        serialWrite("B2A=90 ")
        serialWrite("B2B=90 ")
        serialWrite("B3A=90 ")
        serialWrite("B3B=90 ")
        serialWrite("B4A=90 ")
        serialWrite("B4B=90 ")
        serialWrite("PSARJ=90 ")
        serialWrite("SSARJ=90 ")
        serialWrite("PTRRJ=90 ")
        serialWrite("STRRJ=90 ")

class FakeOrbitScreen(Screen):

    def changeDemoBoolean(self, *args):
        global demoboolean
        demoboolean = args[0]

    def HTVpopup(self, *args): #not fully working
        HTVpopup = Popup(title='HTV Berthing Orbit', content=Label(text='This will playback recorded data from when the Japanese HTV spacecraft berthed to the ISS. During berthing, the SARJs and nadir BGAs lock but the zenith BGAs autotrack'), text_size=self.size, size_hint=(0.5, 0.3), auto_dismiss=True)
        HTVpopup.text_size = self.size
        HTVpopup.open()

    def startDisco(*args):
        global p2, runningDemo, Disco
        if not runningDemo:
            p2 = Popen("/home/pi/Mimic/Pi/disco.sh")
            runningDemo = True
            Disco = True
            logWrite("Successfully started Disco script")

    def startDemo(*args):
        global p2, runningDemo
        if not runningDemo:
            p2 = Popen("/home/pi/Mimic/Pi/demoOrbit.sh")
            runningDemo = True
            logWrite("Successfully started Demo Orbit script")

    def stopDemo(*args):
        global p2, runningDemo
        try:
            p2.kill()
        except Exception:
            pass
        else:
            runningDemo = False

    def startHTVDemo(*args):
        global p2, runningDemo
        if not runningDemo:
            p2 = Popen("/home/pi/Mimic/Pi/demoHTVOrbit.sh")
            runningDemo = True
            logWrite("Successfully started Demo HTV Orbit script")

    def stopHTVDemo(*args):
        global p2, runningDemo
        try:
            p2.kill()
        except Exception:
            pass
        else:
            logWrite("Successfully stopped Demo HTV Orbit script")
            runningDemo = False

class Settings_Screen(Screen, EventDispatcher):
    def checkbox_clicked(*args):
        if args[2]:
            serialWrite("SmartRolloverBGA=1 ")
        else:
            serialWrite("SmartRolloverBGA=0 ")

class Orbit_Screen(Screen, EventDispatcher):
    signalcolor = ObjectProperty([1, 1, 1])

class Orbit_Pass(Screen, EventDispatcher):
    signalcolor = ObjectProperty([1, 1, 1])

class Orbit_Data(Screen, EventDispatcher):
    signalcolor = ObjectProperty([1, 1, 1])

class ISS_Screen(Screen, EventDispatcher):
    signalcolor = ObjectProperty([1, 1, 1])
    def selectModule(*args): #used for choosing a module on screen to light up
        global module
        module = str(args[1])

class ECLSS_Screen(Screen, EventDispatcher):
    signalcolor = ObjectProperty([1, 1, 1])

class EPS_Screen(Screen, EventDispatcher):
    signalcolor = ObjectProperty([1, 1, 1])

class CT_Screen(Screen, EventDispatcher):
    signalcolor = ObjectProperty([1, 1, 1])

class CT_SASA_Screen(Screen, EventDispatcher):
    signalcolor = ObjectProperty([1, 1, 1])

class CT_Camera_Screen(Screen, EventDispatcher):
    signalcolor = ObjectProperty([1, 1, 1])

class CT_UHF_Screen(Screen, EventDispatcher):
    signalcolor = ObjectProperty([1, 1, 1])

class CT_SGANT_Screen(Screen, EventDispatcher):
    signalcolor = ObjectProperty([1, 1, 1])

class GNC_Screen(Screen, EventDispatcher):
    signalcolor = ObjectProperty([1, 1, 1])

class EVA_Main_Screen(Screen, EventDispatcher):
    signalcolor = ObjectProperty([1, 1, 1])

class EVA_US_Screen(Screen, EventDispatcher):
    signalcolor = ObjectProperty([1, 1, 1])

class EVA_RS_Screen(Screen, EventDispatcher):
    signalcolor = ObjectProperty([1, 1, 1])

class EVA_Pictures(Screen, EventDispatcher):
    pass

class TCS_Screen(Screen, EventDispatcher):
    signalcolor = ObjectProperty([1, 1, 1])

class RS_Screen(Screen, EventDispatcher):
    signalcolor = ObjectProperty([1, 1, 1])

class Crew_Screen(Screen, EventDispatcher):
    pass

class MSS_MT_Screen(Screen, EventDispatcher):
    signalcolor = ObjectProperty([1, 1, 1])

class MimicScreen(Screen, EventDispatcher):
    signalcolor = ObjectProperty([1, 1, 1])
    def changeMimicBoolean(self, *args):
        global mimicbutton
        mimicbutton = args[0]

    def startproc(*args):
        global p,TDRSproc
        logWrite("Telemetry Subprocess start")
        p = Popen(["node", "/home/pi/Mimic/Pi/ISS_Telemetry.js"]) #uncomment if live data comes back :D :D :D :D WE SAVED ISSLIVE
        TDRSproc = Popen(["python3", "/home/pi/Mimic/Pi/TDRScheck.py"]) #uncomment if live data comes back :D :D :D :D WE SAVED ISSLIVE
        #p = Popen(["/home/pi/Mimic/Pi/RecordedData/playback.out","/home/pi/Mimic/Pi/RecordedData/Data"])

    def killproc(*args):
        global p,p2,c
        c.execute("INSERT OR IGNORE INTO telemetry VALUES('Lightstreamer', '0', 'Unsubscribed', '0', 0)")
        try:
            p.kill()
            p2.kill()
            TDRSproc.kill()
        except Exception:
            pass

class MainScreenManager(ScreenManager):
    pass

class MainApp(App):

    def build(self):
        global startup, ScreenList, stopAnimation

        self.main_screen = MainScreen(name = 'main')
        self.mimic_screen = MimicScreen(name = 'mimic')
        self.iss_screen = ISS_Screen(name = 'iss')
        self.eclss_screen = ECLSS_Screen(name = 'eclss')
        self.control_screen = ManualControlScreen(name = 'manualcontrol')
        self.orbit_screen = Orbit_Screen(name = 'orbit')
        self.orbit_pass = Orbit_Pass(name = 'orbit_pass')
        self.orbit_data = Orbit_Data(name = 'orbit_data')
        self.fakeorbit_screen = FakeOrbitScreen(name = 'fakeorbit')
        self.eps_screen = EPS_Screen(name = 'eps')
        self.ct_screen = CT_Screen(name = 'ct')
        self.ct_sasa_screen = CT_SASA_Screen(name = 'ct_sasa')
        self.ct_uhf_screen = CT_UHF_Screen(name = 'ct_uhf')
        self.ct_camera_screen = CT_Camera_Screen(name = 'ct_camera')
        self.ct_sgant_screen = CT_SGANT_Screen(name = 'ct_sgant')
        self.gnc_screen = GNC_Screen(name = 'gnc')
        self.tcs_screen = TCS_Screen(name = 'tcs')
        self.crew_screen = Crew_Screen(name = 'crew')
        self.settings_screen = Settings_Screen(name = 'settings')
        self.us_eva = EVA_US_Screen(name='us_eva')
        self.rs_eva = EVA_RS_Screen(name='rs_eva')
        self.rs_screen = RS_Screen(name='rs')
        self.mss_mt_screen = MSS_MT_Screen(name='mt')
        self.eva_main = EVA_Main_Screen(name='eva_main')
        self.eva_pictures = EVA_Pictures(name='eva_pictures')

        #Add all new telemetry screens to this list, this is used for the signal status icon and telemetry value colors
        ScreenList = ['tcs_screen', 'eps_screen', 'iss_screen', 'eclss_screen',
                      'ct_screen', 'ct_sasa_screen', 'ct_sgant_screen', 'ct_uhf_screen',
                      'ct_camera_screen', 'gnc_screen', 'orbit_screen', 'us_eva', 'rs_eva',
                      'eva_main', 'mimic_screen', 'mss_mt_screen','orbit_pass','orbit_data']

        root = MainScreenManager(transition=SwapTransition())
        root.add_widget(self.main_screen)
        root.add_widget(self.control_screen)
        root.add_widget(self.mimic_screen)
        root.add_widget(self.fakeorbit_screen)
        root.add_widget(self.orbit_screen)
        root.add_widget(self.orbit_pass)
        root.add_widget(self.orbit_data)
        root.add_widget(self.iss_screen)
        root.add_widget(self.eclss_screen)
        root.add_widget(self.eps_screen)
        root.add_widget(self.ct_screen)
        root.add_widget(self.ct_sasa_screen)
        root.add_widget(self.ct_uhf_screen)
        root.add_widget(self.ct_camera_screen)
        root.add_widget(self.ct_sgant_screen)
        root.add_widget(self.gnc_screen)
        root.add_widget(self.us_eva)
        root.add_widget(self.rs_eva)
        root.add_widget(self.rs_screen)
        root.add_widget(self.mss_mt_screen)
        root.add_widget(self.eva_main)
        root.add_widget(self.eva_pictures)
        root.add_widget(self.tcs_screen)
        root.add_widget(self.crew_screen)
        root.add_widget(self.settings_screen)
        root.current = 'main' #change this back to main when done with eva setup

        Clock.schedule_interval(self.update_labels, 1) #all telemetry wil refresh and get pushed to arduinos every half second!
        Clock.schedule_interval(self.animate3, 0.1)
        Clock.schedule_interval(self.orbitUpdate, 1)
        Clock.schedule_interval(self.checkCrew, 600)
        if startup:
            startup = False

        Clock.schedule_once(self.checkCrew, 30)
        Clock.schedule_once(self.checkBlogforEVA, 30)
        Clock.schedule_once(self.getTLE, 15) #uncomment when internet works again
        Clock.schedule_once(self.TDRSupdate, 30) #uncomment when internet works again

        Clock.schedule_interval(self.getTLE, 300)
        Clock.schedule_interval(self.TDRSupdate, 600)
        Clock.schedule_interval(self.check_internet, 1)

        #schedule the orbitmap to update with shadow every 5 mins
        Clock.schedule_interval(self.updateNightShade, 120)
        Clock.schedule_interval(self.updateOrbitMap, 10)
        Clock.schedule_interval(self.checkTDRS, 5)
        return root

    def check_internet(self, dt):
        global internet

        def on_success(req, result):
            global internet
            internet = True

        def on_redirect(req, result):
            global internet
            internet = True

        def on_failure(req, result):
            global internet
            internet = False

        def on_error(req, result):
            global internet
            internet = False

        req = UrlRequest("http://google.com", on_success, on_redirect, on_failure, on_error, timeout=1)

    def deleteURLPictures(self, dt):
        logWrite("Function call - deleteURLPictures")
        global EVA_picture_urls
        del EVA_picture_urls[:]
        EVA_picture_urls[:] = []

    def changePictures(self, dt):
        logWrite("Function call - changeURLPictures")
        global EVA_picture_urls
        global urlindex
        urlsize = len(EVA_picture_urls)

        if urlsize > 0:
            self.us_eva.ids.EVAimage.source = EVA_picture_urls[urlindex]
            self.eva_pictures.ids.EVAimage.source = EVA_picture_urls[urlindex]

        urlindex = urlindex + 1
        if urlindex > urlsize-1:
            urlindex = 0
    def updateOrbitMap(self, dt):
        self.orbit_screen.ids.OrbitMap.source = '/home/pi/Mimic/Pi/imgs/orbit/map.jpg'
        self.orbit_screen.ids.OrbitMap.reload()

    def updateNightShade(self, dt):
        proc = Popen(["python3", "/home/pi/Mimic/Pi/NightShade.py"])

    def checkTDRS(self, dt):
        global activeTDRS1
        global activeTDRS2

    def check_EVA_stats(self, lastname1, firstname1, lastname2, firstname2):
        global numEVAs1, EVAtime_hours1, EVAtime_minutes1, numEVAs2, EVAtime_hours2, EVAtime_minutes2
        logWrite("Function call - check EVA stats")
        eva_url = 'http://www.spacefacts.de/eva/e_eva_az.htm'

        def on_success(req, result):
            logWrite("Check EVA Stats - Successs")
            soup = BeautifulSoup(result, 'html.parser') #using bs4 to parse website
            numEVAs1 = 0
            EVAtime_hours1 = 0
            EVAtime_minutes1 = 0
            numEVAs2 = 0
            EVAtime_hours2 = 0
            EVAtime_minutes2 = 0

            tabletags = soup.find_all("td")
            for tag in tabletags:
                if  lastname1 in tag.text:
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

            self.us_eva.ids.EV1.text = " (EV): " + str(firstname1) + " " + str(lastname1)
            self.us_eva.ids.EV2.text = " (EV): " + str(firstname2) + " " + str(lastname2)

            self.us_eva.ids.EV1_EVAnum.text = "Number of EVAs = " + str(EV1_EVA_number)
            self.us_eva.ids.EV2_EVAnum.text = "Number of EVAs = " + str(EV2_EVA_number)
            self.us_eva.ids.EV1_EVAtime.text = "Total EVA Time = " + str(EV1_hours) + "h " + str(EV1_minutes) + "m"
            self.us_eva.ids.EV2_EVAtime.text = "Total EVA Time = " + str(EV2_hours) + "h " + str(EV2_minutes) + "m"

        def on_redirect(req, result):
            logWrite("Warning - EVA stats failure (redirect)")

        def on_failure(req, result):
            logWrite("Warning - EVA stats failure (url failure)")

        def on_error(req, result):
            logWrite("Warning - EVA stats failure (url error)")

        #obtain eva statistics web page for parsing
        req = UrlRequest(eva_url, on_success, on_redirect, on_failure, on_error, timeout=1)

    def checkBlogforEVA(self, dt):
        iss_blog_url =  'https://blogs.nasa.gov/spacestation/tag/spacewalk/'
        def on_success(req, data): #if blog data is successfully received, it is processed here
            logWrite("Blog Success")
            soup = BeautifulSoup(data, "lxml")
            blog_entries = soup.find("div", {"class": "entry-content"})
            blog_text = blog_entries.get_text()

            iss_EVcrew_url = 'https://www.howmanypeopleareinspacerightnow.com/peopleinspace.json'

            def on_success2(req2, data2):
                logWrite("Successfully fetched EV crew JSON")
                number_of_space = int(data2['number'])
                names = []
                for num in range(0, number_of_space):
                    names.append(str(data2['people'][num]['name']))

                try:
                    self.checkBlog(names,blog_text)
                except Exception as e:
                    logWrite("Error checking blog: " + str(e))

            def on_redirect2(req, result):
                logWrite("Warning - Get EVA crew failure (redirect)")
                logWrite(result)

            def on_failure2(req, result):
                logWrite("Warning - Get EVA crew failure (url failure)")

            def on_error2(req, result):
                logWrite("Warning - Get EVA crew failure (url error)")

            req2 = UrlRequest(iss_EVcrew_url, on_success2, on_redirect2, on_failure2, on_error2, timeout=1)

        def on_redirect(req, result):
            logWrite("Warning - Get nasa blog failure (redirect)")

        def on_failure(req, result):
            logWrite("Warning - Get nasa blog failure (url failure)")

        def on_error(req, result):
            logWrite("Warning - Get nasa blog failure (url error)")

        req = UrlRequest(iss_blog_url, on_success, on_redirect, on_failure, on_error, timeout=1)

    def checkBlog(self, names, blog_text): #takes the nasa blog and compares it to people in space
        ev1_surname = ''
        ev1_firstname = ''
        ev2_surname = ''
        ev2_firstname = ''
        ev1name = ''
        ev2name = ''

        name_position = 1000000
        for name in names: #search for text in blog that matchs people in space list, choose 1st result as likely EV1
            if name in blog_text:
                if blog_text.find(name) < name_position:
                    name_position = blog_text.find(name)
                    ev1name = name

        name_position = 1000000

        for name in names: #search for text in blog that matchs people in space list, choose 2nd result as likely EV2
            if name in blog_text and name != ev1name:
                if blog_text.find(name) < name_position:
                    name_position = blog_text.find(name)
                    ev2name = name

        logWrite("Likely EV1: "+ev1name)
        logWrite("Likely EV2: "+ev2name)

        ev1_surname = ev1name.split()[-1]
        ev1_firstname = ev1name.split()[0]
        ev2_surname = ev2name.split()[-1]
        ev2_firstname = ev2name.split()[0]

        try:
            self.check_EVA_stats(ev1_surname,ev1_firstname,ev2_surname,ev2_firstname)
        except Exception as e:
            logWrite("Error retrieving EVA stats: " + str(e))

    def flashUS_EVAbutton(self, instance):
        logWrite("Function call - flashUS_EVA")

        self.eva_main.ids.US_EVA_Button.background_color = (0, 0, 1, 1)
        def reset_color(*args):
            self.eva_main.ids.US_EVA_Button.background_color = (1, 1, 1, 1)
        Clock.schedule_once(reset_color, 0.5)

    def flashRS_EVAbutton(self, instance):
        logWrite("Function call - flashRS_EVA")

        self.eva_main.ids.RS_EVA_Button.background_color = (0, 0, 1, 1)
        def reset_color(*args):
            self.eva_main.ids.RS_EVA_Button.background_color = (1, 1, 1, 1)
        Clock.schedule_once(reset_color, 0.5)

    def flashEVAbutton(self, instance):
        logWrite("Function call - flashEVA")

        self.mimic_screen.ids.EVA_button.background_color = (0, 0, 1, 1)
        def reset_color(*args):
            self.mimic_screen.ids.EVA_button.background_color = (1, 1, 1, 1)
        Clock.schedule_once(reset_color, 0.5)

    def EVA_clock(self, dt):
        global seconds, minutes, hours, EVAstartTime
        unixconvert = time.gmtime(time.time())
        currenthours = float(unixconvert[7])*24+unixconvert[3]+float(unixconvert[4])/60+float(unixconvert[5])/3600
        difference = (currenthours-EVAstartTime)*3600
        minutes, seconds = divmod(difference, 60)
        hours, minutes = divmod(minutes, 60)

        hours = int(hours)
        minutes = int(minutes)
        seconds = int(seconds)

        self.us_eva.ids.EVA_clock.text =(str(hours) + ":" + str(minutes).zfill(2) + ":" + str(int(seconds)).zfill(2))
        self.us_eva.ids.EVA_clock.color = 0.33, 0.7, 0.18

    def animate(self, instance):
        global new_x2, new_y2
        self.main_screen.ids.ISStiny2.size_hint = 0.07, 0.07
        new_x2 = new_x2+0.007
        new_y2 = (math.sin(new_x2*30)/18)+0.75
        if new_x2 > 1:
            new_x2 = new_x2-1.0
        self.main_screen.ids.ISStiny2.pos_hint = {"center_x": new_x2, "center_y": new_y2}

    def animate3(self, instance):
        global new_x, new_y, sizeX, sizeY, startingAnim
        if new_x<0.886:
            new_x = new_x+0.007
            new_y = (math.sin(new_x*30)/18)+0.75
            self.main_screen.ids.ISStiny.pos_hint = {"center_x": new_x, "center_y": new_y}
        else:
            if sizeX <= 0.15:
                sizeX = sizeX + 0.01
                sizeY = sizeY + 0.01
                self.main_screen.ids.ISStiny.size_hint = sizeX, sizeY
            else:
                if startingAnim:
                    Clock.schedule_interval(self.animate, 0.1)
                    startingAnim = False

    def changeColors(self, *args):   #this function sets all labels on mimic screen to a certain color based on signal status
        #the signalcolor is a kv property that will update all signal status dependant values to whatever color is received by this function
        global ScreenList

        for x in ScreenList:
            getattr(self, x).signalcolor = args[0], args[1], args[2]

    def changeManualControlBoolean(self, *args):
        global manualcontrol
        manualcontrol = args[0]

    def TDRSupdate(self, dt):
        global TDRS12_TLE, TDRS6_TLE, TDRS10_TLE, TDRS11_TLE, TDRS7_TLE
        normalizedX = self.orbit_screen.ids.OrbitMap.norm_image_size[0] / self.orbit_screen.ids.OrbitMap.texture_size[0]
        normalizedY = self.orbit_screen.ids.OrbitMap.norm_image_size[1] / self.orbit_screen.ids.OrbitMap.texture_size[1]

        def scaleLatLon(latitude, longitude):
            #converting lat lon to x, y for orbit map
            fromLatSpan = 180.0
            fromLonSpan = 360.0
            toLatSpan = 0.598
            toLonSpan = 0.716
            valueLatScaled = (float(latitude)+90.0)/float(fromLatSpan)
            valueLonScaled = (float(longitude)+180.0)/float(fromLonSpan)
            newLat = (0.265) + (valueLatScaled * toLatSpan)
            newLon = (0.14) + (valueLonScaled * toLonSpan)
            return {'newLat': newLat, 'newLon': newLon}

        def scaleLatLon2(in_latitude,in_longitude):
            MAP_HEIGHT = self.orbit_screen.ids.OrbitMap.texture_size[1]
            MAP_WIDTH = self.orbit_screen.ids.OrbitMap.texture_size[0]

            new_x = ((MAP_WIDTH / 360.0) * (180 + in_longitude))
            new_y = ((MAP_HEIGHT / 180.0) * (90 + in_latitude))
            return {'new_y': new_y, 'new_x': new_x}

        #TDRS East 2 sats
        try:
            TDRS12_TLE.compute(datetime.utcnow()) #41 West
        except NameError:
            TDRS12lon = -41
            TDRS12lat = 0
        else:
            TDRS12lon = float(str(TDRS12_TLE.sublong).split(':')[0]) + float(str(TDRS12_TLE.sublong).split(':')[1])/60 + float(str(TDRS12_TLE.sublong).split(':')[2])/3600
            TDRS12lat = float(str(TDRS12_TLE.sublat).split(':')[0]) + float(str(TDRS12_TLE.sublat).split(':')[1])/60 + float(str(TDRS12_TLE.sublat).split(':')[2])/3600
            TDRS12_groundtrack = []
            date_i = datetime.utcnow()
            groundtrackdate = datetime.utcnow()
            while date_i < groundtrackdate + timedelta(days=1):
                TDRS12_TLE.compute(date_i)

                TDRS12lon_gt = float(str(TDRS12_TLE.sublong).split(':')[0]) + float(
                    str(TDRS12_TLE.sublong).split(':')[1]) / 60 + float(str(TDRS12_TLE.sublong).split(':')[2]) / 3600
                TDRS12lat_gt = float(str(TDRS12_TLE.sublat).split(':')[0]) + float(
                    str(TDRS12_TLE.sublat).split(':')[1]) / 60 + float(str(TDRS12_TLE.sublat).split(':')[2]) / 3600

                TDRS12_groundtrack.append(scaleLatLon2(TDRS12lat_gt, TDRS12lon_gt)['new_x'])
                TDRS12_groundtrack.append(scaleLatLon2(TDRS12lat_gt, TDRS12lon_gt)['new_y'])

                date_i += timedelta(minutes=10)

            self.orbit_screen.ids.TDRS12groundtrack.width = 1
            self.orbit_screen.ids.TDRS12groundtrack.col = (0,0,1,1)
            self.orbit_screen.ids.TDRS12groundtrack.points = TDRS12_groundtrack

        try:
            TDRS6_TLE.compute(datetime.utcnow()) #46 West
        except NameError:
            TDRS6lon = -46
            TDRS6lat = 0
        else:
            TDRS6lon = float(str(TDRS6_TLE.sublong).split(':')[0]) + float(str(TDRS6_TLE.sublong).split(':')[1])/60 + float(str(TDRS6_TLE.sublong).split(':')[2])/3600
            TDRS6lat = float(str(TDRS6_TLE.sublat).split(':')[0]) + float(str(TDRS6_TLE.sublat).split(':')[1])/60 + float(str(TDRS6_TLE.sublat).split(':')[2])/3600
            TDRS6_groundtrack = []
            date_i = datetime.utcnow()
            groundtrackdate = datetime.utcnow()
            while date_i < groundtrackdate + timedelta(days=1):
                TDRS6_TLE.compute(date_i)

                TDRS6lon_gt = float(str(TDRS6_TLE.sublong).split(':')[0]) + float(
                    str(TDRS6_TLE.sublong).split(':')[1]) / 60 + float(str(TDRS6_TLE.sublong).split(':')[2]) / 3600
                TDRS6lat_gt = float(str(TDRS6_TLE.sublat).split(':')[0]) + float(
                    str(TDRS6_TLE.sublat).split(':')[1]) / 60 + float(str(TDRS6_TLE.sublat).split(':')[2]) / 3600

                TDRS6_groundtrack.append(scaleLatLon2(TDRS6lat_gt, TDRS6lon_gt)['new_x'])
                TDRS6_groundtrack.append(scaleLatLon2(TDRS6lat_gt, TDRS6lon_gt)['new_y'])

                date_i += timedelta(minutes=10)

            self.orbit_screen.ids.TDRS6groundtrack.width = 1
            self.orbit_screen.ids.TDRS6groundtrack.col = (0,0,1,1)
            self.orbit_screen.ids.TDRS6groundtrack.points = TDRS6_groundtrack

        #TDRS West 2 sats
        try:
            TDRS11_TLE.compute(datetime.utcnow()) #171 West
        except NameError:
            TDRS11lon = -171
            TDRS11lat = 0
        else:
            TDRS11lon = float(str(TDRS11_TLE.sublong).split(':')[0]) + float(str(TDRS11_TLE.sublong).split(':')[1])/60 + float(str(TDRS11_TLE.sublong).split(':')[2])/3600
            TDRS11lat = float(str(TDRS11_TLE.sublat).split(':')[0]) + float(str(TDRS11_TLE.sublat).split(':')[1])/60 + float(str(TDRS11_TLE.sublat).split(':')[2])/3600
            TDRS11_groundtrack = []
            date_i = datetime.utcnow()
            groundtrackdate = datetime.utcnow()
            while date_i < groundtrackdate + timedelta(days=1):
                TDRS11_TLE.compute(date_i)

                TDRS11lon_gt = float(str(TDRS11_TLE.sublong).split(':')[0]) + float(
                    str(TDRS11_TLE.sublong).split(':')[1]) / 60 + float(str(TDRS11_TLE.sublong).split(':')[2]) / 3600
                TDRS11lat_gt = float(str(TDRS11_TLE.sublat).split(':')[0]) + float(
                    str(TDRS11_TLE.sublat).split(':')[1]) / 60 + float(str(TDRS11_TLE.sublat).split(':')[2]) / 3600

                TDRS11_groundtrack.append(scaleLatLon2(TDRS11lat_gt, TDRS11lon_gt)['new_x'])
                TDRS11_groundtrack.append(scaleLatLon2(TDRS11lat_gt, TDRS11lon_gt)['new_y'])

                date_i += timedelta(minutes=10)

            self.orbit_screen.ids.TDRS11groundtrack.width = 1
            self.orbit_screen.ids.TDRS11groundtrack.col = (0,0,1,1)
            self.orbit_screen.ids.TDRS11groundtrack.points = TDRS11_groundtrack

        try:
            TDRS10_TLE.compute(datetime.utcnow()) #174 West
        except NameError:
            TDRS10lon = -174
            TDRS10lat = 0
        else:
            TDRS10lon = float(str(TDRS10_TLE.sublong).split(':')[0]) + float(str(TDRS10_TLE.sublong).split(':')[1])/60 + float(str(TDRS10_TLE.sublong).split(':')[2])/3600
            TDRS10lat = float(str(TDRS10_TLE.sublat).split(':')[0]) + float(str(TDRS10_TLE.sublat).split(':')[1])/60 + float(str(TDRS10_TLE.sublat).split(':')[2])/3600
            TDRS10_groundtrack = []
            date_i = datetime.utcnow()
            groundtrackdate = datetime.utcnow()
            while date_i < groundtrackdate + timedelta(days=1):
                TDRS10_TLE.compute(date_i)

                TDRS10lon_gt = float(str(TDRS10_TLE.sublong).split(':')[0]) + float(
                    str(TDRS10_TLE.sublong).split(':')[1]) / 60 + float(str(TDRS10_TLE.sublong).split(':')[2]) / 3600
                TDRS10lat_gt = float(str(TDRS10_TLE.sublat).split(':')[0]) + float(
                    str(TDRS10_TLE.sublat).split(':')[1]) / 60 + float(str(TDRS10_TLE.sublat).split(':')[2]) / 3600

                TDRS10_groundtrack.append(scaleLatLon2(TDRS10lat_gt, TDRS10lon_gt)['new_x'])
                TDRS10_groundtrack.append(scaleLatLon2(TDRS10lat_gt, TDRS10lon_gt)['new_y'])

                date_i += timedelta(minutes=10)

            self.orbit_screen.ids.TDRS10groundtrack.width = 1
            self.orbit_screen.ids.TDRS10groundtrack.col = (0,0,1,1)
            self.orbit_screen.ids.TDRS10groundtrack.points = TDRS10_groundtrack

        #ZOE TDRS-Z
        try:
            TDRS7_TLE.compute(datetime.utcnow()) #275 West
        except NameError:
            TDRS7lon = 85
            TDRS7lat = 0
        else:
            TDRS7lon = float(str(TDRS7_TLE.sublong).split(':')[0]) + float(str(TDRS7_TLE.sublong).split(':')[1])/60 + float(str(TDRS7_TLE.sublong).split(':')[2])/3600
            TDRS7lat = float(str(TDRS7_TLE.sublat).split(':')[0]) + float(str(TDRS7_TLE.sublat).split(':')[1])/60 + float(str(TDRS7_TLE.sublat).split(':')[2])/3600
            TDRS7_groundtrack = []
            date_i = datetime.utcnow()
            groundtrackdate = datetime.utcnow()
            while date_i < groundtrackdate + timedelta(days=1):
                TDRS7_TLE.compute(date_i)

                TDRS7lon_gt = float(str(TDRS7_TLE.sublong).split(':')[0]) + float(
                    str(TDRS7_TLE.sublong).split(':')[1]) / 60 + float(str(TDRS7_TLE.sublong).split(':')[2]) / 3600
                TDRS7lat_gt = float(str(TDRS7_TLE.sublat).split(':')[0]) + float(
                    str(TDRS7_TLE.sublat).split(':')[1]) / 60 + float(str(TDRS7_TLE.sublat).split(':')[2]) / 3600

                TDRS7_groundtrack.append(scaleLatLon2(TDRS7lat_gt, TDRS7lon_gt)['new_x'])
                TDRS7_groundtrack.append(scaleLatLon2(TDRS7lat_gt, TDRS7lon_gt)['new_y'])

                date_i += timedelta(minutes=10)

            self.orbit_screen.ids.TDRS7groundtrack.width = 1
            self.orbit_screen.ids.TDRS7groundtrack.col = (0,0,1,1)
            self.orbit_screen.ids.TDRS7groundtrack.points = TDRS7_groundtrack

        #draw the TDRS satellite locations
        self.orbit_screen.ids.TDRS12.pos = (scaleLatLon2(TDRS12lat, TDRS12lon)['new_x']-((self.orbit_screen.ids.TDRS12.width/2)*normalizedX),scaleLatLon2(TDRS12lat, TDRS12lon)['new_y']-((self.orbit_screen.ids.TDRS12.height/2)*normalizedY))
        self.orbit_screen.ids.TDRS6.pos = (scaleLatLon2(TDRS6lat, TDRS6lon)['new_x']-((self.orbit_screen.ids.TDRS6.width/2)*normalizedX),scaleLatLon2(TDRS6lat, TDRS6lon)['new_y']-((self.orbit_screen.ids.TDRS6.height/2)*normalizedY))
        self.orbit_screen.ids.TDRS11.pos = (scaleLatLon2(TDRS11lat, TDRS11lon)['new_x']-((self.orbit_screen.ids.TDRS11.width/2)*normalizedX),scaleLatLon2(TDRS11lat, TDRS11lon)['new_y']-((self.orbit_screen.ids.TDRS11.height/2)*normalizedY))
        self.orbit_screen.ids.TDRS10.pos = (scaleLatLon2(TDRS10lat, TDRS10lon)['new_x']-((self.orbit_screen.ids.TDRS10.width/2)*normalizedX),scaleLatLon2(TDRS10lat, TDRS10lon)['new_y']-((self.orbit_screen.ids.TDRS10.height/2)*normalizedY))
        self.orbit_screen.ids.TDRS7.pos = (scaleLatLon2(TDRS7lat, TDRS7lon)['new_x']-((self.orbit_screen.ids.TDRS7.width/2)*normalizedX),scaleLatLon2(TDRS7lat, TDRS7lon)['new_y']-((self.orbit_screen.ids.TDRS7.height/2)*normalizedY))
        #add labels and ZOE
        self.orbit_screen.ids.TDRSeLabel.pos_hint = {"center_x": scaleLatLon(0, -41)['newLon']+0.06, "center_y": scaleLatLon(0, -41)['newLat']}
        self.orbit_screen.ids.TDRSwLabel.pos_hint = {"center_x": scaleLatLon(0, -174)['newLon']+0.06, "center_y": scaleLatLon(0, -174)['newLat']}
        self.orbit_screen.ids.TDRSzLabel.pos_hint = {"center_x": scaleLatLon(0, 85)['newLon']+0.05, "center_y": scaleLatLon(0, 85)['newLat']}
        self.orbit_screen.ids.ZOE.pos_hint = {"center_x": scaleLatLon(0, 77)['newLon'], "center_y": scaleLatLon(0, 77)['newLat']}
        self.orbit_screen.ids.ZOElabel.pos_hint = {"center_x": scaleLatLon(0, 77)['newLon'], "center_y": scaleLatLon(0, 77)['newLat']+0.1}

    def orbitUpdate(self, dt):
        global overcountry, ISS_TLE, ISS_TLE_Line1, ISS_TLE_Line2, ISS_TLE_Acquired, sgant_elevation, sgant_elevation_old, sgant_xelevation, aos, oldtdrs, tdrs, logged
        global TDRS12_TLE, TDRS6_TLE, TDRS7_TLE, TDRS10_TLE, TDRS11_TLE, tdrs1, tdrs2, tdrs_timestamp
        def scaleLatLon(latitude, longitude):
            #converting lat lon to x, y for orbit map
            fromLatSpan = 180.0
            fromLonSpan = 360.0
            toLatSpan = 0.598
            toLonSpan = 0.716
            valueLatScaled = (float(latitude)+90.0)/float(fromLatSpan)
            valueLonScaled = (float(longitude)+180.0)/float(fromLonSpan)
            newLat = (0.265) + (valueLatScaled * toLatSpan)
            newLon = (0.14) + (valueLonScaled * toLonSpan)
            return {'newLat': newLat, 'newLon': newLon}

        def scaleLatLon2(in_latitude,in_longitude):
            MAP_HEIGHT = self.orbit_screen.ids.OrbitMap.texture_size[1]
            MAP_WIDTH = self.orbit_screen.ids.OrbitMap.texture_size[0]

            new_x = ((MAP_WIDTH / 360.0) * (180 + in_longitude))
            new_y = ((MAP_HEIGHT / 180.0) * (90 + in_latitude))
            return {'new_y': new_y, 'new_x': new_x}

        #copied from apexpy - copyright 2015 Christer van der Meeren MIT license
        def subsolar(datetime):

            year = datetime.year
            doy = datetime.timetuple().tm_yday
            ut = datetime.hour * 3600 + datetime.minute * 60 + datetime.second

            if not 1601 <= year <= 2100:
                raise ValueError('Year must be in [1601, 2100]')

            yr = year - 2000

            nleap = int(np.floor((year - 1601.0) / 4.0))
            nleap -= 99
            if year <= 1900:
                ncent = int(np.floor((year - 1601.0) / 100.0))
                ncent = 3 - ncent
                nleap = nleap + ncent

            l0 = -79.549 + (-0.238699 * (yr - 4.0 * nleap) + 3.08514e-2 * nleap)
            g0 = -2.472 + (-0.2558905 * (yr - 4.0 * nleap) - 3.79617e-2 * nleap)

            # Days (including fraction) since 12 UT on January 1 of IYR:
            df = (ut / 86400.0 - 1.5) + doy

            # Mean longitude of Sun:
            lmean = l0 + 0.9856474 * df

            # Mean anomaly in radians:
            grad = np.radians(g0 + 0.9856003 * df)

            # Ecliptic longitude:
            lmrad = np.radians(lmean + 1.915 * np.sin(grad)
                               + 0.020 * np.sin(2.0 * grad))
            sinlm = np.sin(lmrad)

            # Obliquity of ecliptic in radians:
            epsrad = np.radians(23.439 - 4e-7 * (df + 365 * yr + nleap))

            # Right ascension:
            alpha = np.degrees(np.arctan2(np.cos(epsrad) * sinlm, np.cos(lmrad)))

            # Declination, which is also the subsolar latitude:
            sslat = np.degrees(np.arcsin(np.sin(epsrad) * sinlm))

            # Equation of time (degrees):
            etdeg = lmean - alpha
            nrot = round(etdeg / 360.0)
            etdeg = etdeg - 360.0 * nrot

            # Subsolar longitude:
            sslon = 180.0 - (ut / 240.0 + etdeg) # Earth rotates one degree every 240 s.
            nrot = round(sslon / 360.0)
            sslon = sslon - 360.0 * nrot

            return sslat, sslon

        if ISS_TLE_Acquired:
            ISS_TLE.compute(datetime.utcnow())
            #------------------Latitude/Longitude Stuff---------------------------
            latitude = float(str(ISS_TLE.sublat).split(':')[0]) + float(str(ISS_TLE.sublat).split(':')[1])/60 + float(str(ISS_TLE.sublat).split(':')[2])/3600
            longitude = float(str(ISS_TLE.sublong).split(':')[0]) + float(str(ISS_TLE.sublong).split(':')[1])/60 + float(str(ISS_TLE.sublong).split(':')[2])/3600

            #inclination = ISS_TLE.inc

            normalizedX = self.orbit_screen.ids.OrbitMap.norm_image_size[0] / self.orbit_screen.ids.OrbitMap.texture_size[0]
            normalizedY = self.orbit_screen.ids.OrbitMap.norm_image_size[1] / self.orbit_screen.ids.OrbitMap.texture_size[1]

            self.orbit_screen.ids.OrbitISStiny.pos = (
                    scaleLatLon2(latitude, longitude)['new_x'] - ((self.orbit_screen.ids.OrbitISStiny.width / 2) * normalizedX * 2), #had to fudge a little not sure why
                    scaleLatLon2(latitude, longitude)['new_y'] - ((self.orbit_screen.ids.OrbitISStiny.height / 2) * normalizedY * 2)) #had to fudge a little not sure why

            #get the position of the sub solar point to add the sun icon to the map
            sunlatitude, sunlongitude = subsolar(datetime.utcnow())

            self.orbit_screen.ids.OrbitSun.pos = (
                    scaleLatLon2(int(sunlatitude), int(sunlongitude))['new_x'] - ((self.orbit_screen.ids.OrbitSun.width / 2) * normalizedX * 2), #had to fudge a little not sure why
                    scaleLatLon2(int(sunlatitude), int(sunlongitude))['new_y'] - ((self.orbit_screen.ids.OrbitSun.height / 2) * normalizedY * 2)) #had to fudge a little not sure why

            #draw the ISS groundtrack behind and ahead of the 180 longitude cutoff
            ISS_groundtrack = []
            ISS_groundtrack2 = []
            date_i = datetime.utcnow()
            groundtrackdate = datetime.utcnow()
            while date_i < groundtrackdate + timedelta(minutes=95):
                ISS_TLE.compute(date_i)

                ISSlon_gt = float(str(ISS_TLE.sublong).split(':')[0]) + float(
                    str(ISS_TLE.sublong).split(':')[1]) / 60 + float(str(ISS_TLE.sublong).split(':')[2]) / 3600
                ISSlat_gt = float(str(ISS_TLE.sublat).split(':')[0]) + float(
                    str(ISS_TLE.sublat).split(':')[1]) / 60 + float(str(ISS_TLE.sublat).split(':')[2]) / 3600

                if ISSlon_gt < longitude-1: #if the propagated groundtrack is behind the iss (i.e. wraps around the screen) add to new groundtrack line
                    ISS_groundtrack2.append(scaleLatLon2(ISSlat_gt, ISSlon_gt)['new_x'])
                    ISS_groundtrack2.append(scaleLatLon2(ISSlat_gt, ISSlon_gt)['new_y'])
                else:
                    ISS_groundtrack.append(scaleLatLon2(ISSlat_gt, ISSlon_gt)['new_x'])
                    ISS_groundtrack.append(scaleLatLon2(ISSlat_gt, ISSlon_gt)['new_y'])

                date_i += timedelta(seconds=60)

            self.orbit_screen.ids.ISSgroundtrack.width = 1
            self.orbit_screen.ids.ISSgroundtrack.col = (1, 0, 0, 1)
            self.orbit_screen.ids.ISSgroundtrack.points = ISS_groundtrack

            self.orbit_screen.ids.ISSgroundtrack2.width = 1
            self.orbit_screen.ids.ISSgroundtrack2.col = (1, 0, 0, 1)
            self.orbit_screen.ids.ISSgroundtrack2.points = ISS_groundtrack2

            self.orbit_screen.ids.latitude.text = str("{:.2f}".format(latitude))
            self.orbit_screen.ids.longitude.text = str("{:.2f}".format(longitude))

            TDRScursor.execute('select TDRS1 from tdrs')
            tdrs1 = int(TDRScursor.fetchone()[0])
            TDRScursor.execute('select TDRS2 from tdrs')
            tdrs2 = int(TDRScursor.fetchone()[0])
            TDRScursor.execute('select Timestamp from tdrs')
            tdrs_timestamp = TDRScursor.fetchone()[0]

            # THIS SECTION NEEDS IMPROVEMENT
            tdrs = "n/a"
            self.ct_sgant_screen.ids.tdrs_east12.angle = (-1*longitude)-41
            self.ct_sgant_screen.ids.tdrs_east6.angle = (-1*longitude)-46
            self.ct_sgant_screen.ids.tdrs_z7.angle = ((-1*longitude)-41)+126
            self.ct_sgant_screen.ids.tdrs_west11.angle = ((-1*longitude)-41)-133
            self.ct_sgant_screen.ids.tdrs_west10.angle = ((-1*longitude)-41)-130

            if ((tdrs1 or tdrs2) == 12) and float(aos) == 1.0:
                tdrs = "east-12"
                self.ct_sgant_screen.ids.tdrs_label.text = "TDRS-East-12"
            if ((tdrs1 or tdrs2) == 6) and float(aos) == 1.0:
                tdrs = "east-6"
                self.ct_sgant_screen.ids.tdrs_label.text = "TDRS-East-6"
            if ((tdrs1 or tdrs2) == 10) and float(aos) == 1.0:
                tdrs = "west-10"
                self.ct_sgant_screen.ids.tdrs_label.text = "TDRS-West-10"
            if ((tdrs1 or tdrs2) == 11) and float(aos) == 1.0:
                tdrs = "west-11"
                self.ct_sgant_screen.ids.tdrs_label.text = "TDRS-West-11"
            if ((tdrs1 or tdrs2) == 7) and float(aos) == 1.0:
                tdrs = "z-7"
                self.ct_sgant_screen.ids.tdrs_label.text = "TDRS-Z-7"
            elif tdrs1 == 0 and tdrs2 == 0:
                self.ct_sgant_screen.ids.tdrs_label.text = "-"
                tdrs = "----"

            self.ct_sgant_screen.ids.tdrs_z7.color = 1, 1, 1, 1
            self.orbit_screen.ids.TDRSwLabel.color = (1,1,1,1)
            self.orbit_screen.ids.TDRSeLabel.color = (1,1,1,1)
            self.orbit_screen.ids.TDRSzLabel.color = (1,1,1,1)
            self.orbit_screen.ids.TDRS11.col = (1,1,1,1)
            self.orbit_screen.ids.TDRS10.col = (1,1,1,1)
            self.orbit_screen.ids.TDRS12.col = (1,1,1,1)
            self.orbit_screen.ids.TDRS6.col = (1,1,1,1)
            self.orbit_screen.ids.TDRS7.col = (1,1,1,1)
            self.orbit_screen.ids.ZOElabel.color = (1,1,1,1)
            self.orbit_screen.ids.ZOE.col = (1,0.5,0,0.5)

            if "10" in tdrs: #tdrs10 and 11 west
                self.orbit_screen.ids.TDRSwLabel.color = (1,0,1,1)
                self.orbit_screen.ids.TDRS10.col = (1,0,1,1)
            if "11" in tdrs: #tdrs10 and 11 west
                self.orbit_screen.ids.TDRSwLabel.color = (1,0,1,1)
                self.orbit_screen.ids.TDRS11.col = (1,0,1,1)
                self.orbit_screen.ids.TDRS10.col = (1,1,1,1)
            if "6" in tdrs: #tdrs6 and 12 east
                self.orbit_screen.ids.TDRSeLabel.color = (1,0,1,1)
                self.orbit_screen.ids.TDRS6.col = (1,0,1,1)
            if "12" in tdrs: #tdrs6 and 12 east
                self.orbit_screen.ids.TDRSeLabel.color = (1,0,1,1)
                self.orbit_screen.ids.TDRS12.col = (1,0,1,1)
            if "7" in tdrs: #tdrs7 z
                self.ct_sgant_screen.ids.tdrs_z7.color = 1, 1, 1, 1
                self.orbit_screen.ids.TDRSzLabel.color = (1,0,1,1)
                self.orbit_screen.ids.TDRS7.col = (1,0,1,1)
                self.orbit_screen.ids.ZOElabel.color = 0, 0, 0, 0
                self.orbit_screen.ids.ZOE.col = (0,0,0,0)

            #------------------Orbit Stuff---------------------------
            now = datetime.utcnow()
            mins = (now - now.replace(hour=0,minute=0,second=0,microsecond=0)).total_seconds()
            orbits_today = math.floor((float(mins)/60)/90)
            self.orbit_screen.ids.dailyorbit.text = str(int(orbits_today)) #display number of orbits since utc midnight

            year = int('20' + str(ISS_TLE_Line1[18:20]))
            decimal_days = float(ISS_TLE_Line1[20:32])
            converted_time = datetime(year, 1 ,1) + timedelta(decimal_days - 1)
            time_since_epoch = ((now - converted_time).total_seconds()) #convert time difference to hours
            totalorbits = int(ISS_TLE_Line2[63:68]) + 100000 + int(float(time_since_epoch)/(90*60)) #add number of orbits since the tle was generated
            self.orbit_screen.ids.totalorbits.text = str(totalorbits) #display number of orbits since utc midnight
            #------------------ISS Pass Detection---------------------------
            location = ephem.Observer()
            location.lon         = '-95:21:59' #will next to make these an input option
            location.lat         = '29:45:43'
            location.elevation   = 10
            location.name        = 'location'
            location.horizon    = '10'
            location.pressure = 0
            location.date = datetime.utcnow()

            #use location to draw dot on orbit map
            mylatitude = float(str(location.lat).split(':')[0]) + float(str(location.lat).split(':')[1])/60 + float(str(location.lat).split(':')[2])/3600
            mylongitude = float(str(location.lon).split(':')[0]) + float(str(location.lon).split(':')[1])/60 + float(str(location.lon).split(':')[2])/3600
            self.orbit_screen.ids.mylocation.col = (0,0,1,1)
            self.orbit_screen.ids.mylocation.pos = (scaleLatLon2(mylatitude, mylongitude)['new_x']-((self.orbit_screen.ids.mylocation.width/2)*normalizedX),scaleLatLon2(mylatitude, mylongitude)['new_y']-((self.orbit_screen.ids.mylocation.height/2)*normalizedY))

            def isVisible(pass_info):
                def seconds_between(d1, d2):
                    return abs((d2 - d1).seconds)

                def datetime_from_time(tr):
                    year, month, day, hour, minute, second = tr.tuple()
                    dt = dtime.datetime(year, month, day, hour, minute, int(second))
                    return dt

                tr, azr, tt, altt, ts, azs = pass_info
                max_time = datetime_from_time(tt)

                location.date = max_time

                sun = ephem.Sun()
                sun.compute(location)
                ISS_TLE.compute(location)
                sun_alt = float(str(sun.alt).split(':')[0]) + float(str(sun.alt).split(':')[1])/60 + float(str(sun.alt).split(':')[2])/3600
                visible = False
                if ISS_TLE.eclipsed is False and -18 < sun_alt < -6:
                    visible = True
                #on the pass screen add info for why not visible
                return visible

            ISS_TLE.compute(location) #compute tle propagation based on provided location
            nextpassinfo = location.next_pass(ISS_TLE)

            if nextpassinfo[0] is None:
                self.orbit_screen.ids.iss_next_pass1.text = "n/a"
                self.orbit_screen.ids.iss_next_pass2.text = "n/a"
                self.orbit_screen.ids.countdown.text = "n/a"
            else:
                nextpassdatetime = datetime.strptime(str(nextpassinfo[0]), '%Y/%m/%d %H:%M:%S') #convert to datetime object for timezone conversion
                nextpassinfo_format = nextpassdatetime.replace(tzinfo=pytz.utc)
                localtimezone = pytz.timezone('America/Chicago')
                localnextpass = nextpassinfo_format.astimezone(localtimezone)
                self.orbit_screen.ids.iss_next_pass1.text = str(localnextpass).split()[0] #display next pass time
                self.orbit_screen.ids.iss_next_pass2.text = str(localnextpass).split()[1].split('-')[0] #display next pass time
                timeuntilnextpass = nextpassinfo[0] - location.date
                nextpasshours = timeuntilnextpass*24.0
                nextpassmins = (nextpasshours-math.floor(nextpasshours))*60
                nextpassseconds = (nextpassmins-math.floor(nextpassmins))*60
                if isVisible(nextpassinfo):
                    self.orbit_screen.ids.ISSvisible.text = "Visible Pass!"
                else:
                    self.orbit_screen.ids.ISSvisible.text = "Not Visible"
                self.orbit_screen.ids.countdown.text = str("{:.0f}".format(math.floor(nextpasshours))) + ":" + str("{:.0f}".format(math.floor(nextpassmins))) + ":" + str("{:.0f}".format(math.floor(nextpassseconds))) #display time until next pass

    def getTLE(self, *args):
        global ISS_TLE, ISS_TLE_Line1, ISS_TLE_Line2, ISS_TLE_Acquired
        #iss_tle_url =  'https://spaceflight.nasa.gov/realdata/sightings/SSapplications/Post/JavaSSOP/orbit/ISS/SVPOST.html' #the rev counter on this page is wrong
        iss_tle_url =  'https://www.celestrak.com/NORAD/elements/stations.txt'
        tdrs_tle_url =  'https://www.celestrak.com/NORAD/elements/tdrss.txt'

        def on_success(req, data): #if TLE data is successfully received, it is processed here
            global ISS_TLE, ISS_TLE_Line1, ISS_TLE_Line2, ISS_TLE_Acquired
            soup = BeautifulSoup(data, "lxml")
            body = iter(soup.get_text().split('\n'))
            results = []
            for line in body:
                if "ISS (ZARYA)" in line:
                    results.append(line)
                    results.append(next(body))
                    results.append(next(body))
                    break
            results = [i.strip() for i in results]

            if len(results) > 0:
                ISS_TLE_Line1 = results[1]
                ISS_TLE_Line2 = results[2]
                ISS_TLE = ephem.readtle("ISS (ZARYA)", str(ISS_TLE_Line1), str(ISS_TLE_Line2))
                ISS_TLE_Acquired = True
                logWrite("ISS TLE Acquired!")
            else:
                logWrite("ISS TLE Not Acquired")
                ISS_TLE_Acquired = False

        def on_redirect(req, result):
            logWrite("Warning - Get ISS TLE failure (redirect)")

        def on_failure(req, result):
            logWrite("Warning - Get ISS TLE failure (url failure)")

        def on_error(req, result):
            logWrite("Warning - Get ISS TLE failure (url error)")

        def on_success2(req2, data2): #if TLE data is successfully received, it is processed here
            #retrieve the TLEs for every TDRS that ISS talks too
            global TDRS12_TLE,TDRS6_TLE,TDRS11_TLE,TDRS10_TLE,TDRS7_TLE
            soup = BeautifulSoup(data2, "lxml")
            body = iter(soup.get_text().split('\n'))
            results = ['','','']
            #TDRS 12 TLE
            for line in body:
                if "TDRS 12" in line:
                    results[0] = line
                    results[1] = next(body)
                    results[2] = next(body)
                    break

            if len(results[1]) > 0:
                TDRS12_TLE = ephem.readtle("TDRS 12", str(results[1]), str(results[2]))
                logWrite("TDRS 12 TLE Success!")
            else:
                logWrite("TDRS 12 TLE not acquired")

            results = ['','','']
            body = iter(soup.get_text().split('\n'))
            #TDRS 6 TLE
            for line in body:
                if "TDRS 6" in line:
                    results[0] = line
                    results[1] = next(body)
                    results[2] = next(body)
                    break

            if len(results[1]) > 0:
                TDRS6_TLE = ephem.readtle("TDRS 6", str(results[1]), str(results[2]))
                logWrite("TDRS 6 TLE Success!")
            else:
                logWrite("TDRS 6 TLE not acquired")

            results = ['','','']
            body = iter(soup.get_text().split('\n'))
            #TDRS 11 TLE
            for line in body:
                if "TDRS 11" in line:
                    results[0] = line
                    results[1] = next(body)
                    results[2] = next(body)
                    break

            if len(results[1]) > 0:
                TDRS11_TLE = ephem.readtle("TDRS 11", str(results[1]), str(results[2]))
                logWrite("TDRS 11 TLE Success!")
            else:
                logWrite("TDRS 11 TLE not acquired")

            results = ['','','']
            body = iter(soup.get_text().split('\n'))
            #TDRS 10 TLE
            for line in body:
                if "TDRS 10" in line:
                    results[0] = line
                    results[1] = next(body)
                    results[2] = next(body)
                    break

            if len(results[1]) > 0:
                TDRS10_TLE = ephem.readtle("TDRS 10", str(results[1]), str(results[2]))
                logWrite("TDRS 10 TLE Success!")
            else:
                logWrite("TDRS 10 TLE not acquired")

            results = ['','','']
            body = iter(soup.get_text().split('\n'))
            #TDRS 7 TLE
            for line in body:
                if "TDRS 7" in line:
                    results[0] = line
                    results[1] = next(body)
                    results[2] = next(body)
                    break

            if len(results[1]) > 0:
                TDRS7_TLE = ephem.readtle("TDRS 7", str(results[1]), str(results[2]))
                logWrite("TDRS 7 TLE Success!")
            else:
                logWrite("TDRS 7 TLE not acquired")

        def on_redirect2(req2, result):
            logWrite("Warning - Get ISS TLE failure (redirect)")

        def on_failure2(req2, result):
            logWrite("Warning - Get ISS TLE failure (url failure)")

        def on_error2(req2, result):
            logWrite("Warning - Get ISS TLE failure (url error)")

        req = UrlRequest(iss_tle_url, on_success, on_redirect, on_failure, on_error, timeout=1)
        req2 = UrlRequest(tdrs_tle_url, on_success2, on_redirect2, on_failure2, on_error2, timeout=1)

    def checkCrew(self, dt):
        iss_crew_url = 'https://www.howmanypeopleareinspacerightnow.com/peopleinspace.json'
        urlsuccess = False

        def on_success(req, data):
            logWrite("Successfully fetched crew JSON")
            isscrew = 0
            crewmember = ['', '', '', '', '', '', '', '', '', '', '', '']
            crewmemberbio = ['', '', '', '', '', '', '', '', '', '', '', '']
            crewmembertitle = ['', '', '', '', '', '', '', '', '', '', '', '']
            crewmemberdays = ['', '', '', '', '', '', '', '', '', '', '', '']
            crewmemberpicture = ['', '', '', '', '', '', '', '', '', '', '', '']
            crewmembercountry = ['', '', '', '', '', '', '', '', '', '', '', '']
            now = datetime.utcnow()
            number_of_space = int(data['number'])
            for num in range(1, number_of_space+1):
                if str(data['people'][num-1]['location']) == str("International Space Station"):
                    crewmember[isscrew] = str(data['people'][num-1]['name']) #.encode('utf-8')
                    crewmemberbio[isscrew] = str(data['people'][num-1]['bio'])
                    crewmembertitle[isscrew] = str(data['people'][num-1]['title'])
                    datetime_object = datetime.strptime(str(data['people'][num-1]['launchdate']), '%Y-%m-%d')
                    previousdays = int(data['people'][num-1]['careerdays'])
                    totaldaysinspace = str(now-datetime_object)
                    d_index = totaldaysinspace.index('d')
                    crewmemberdays[isscrew] = str(int(totaldaysinspace[:d_index])+previousdays)+" days in space"
                    crewmemberpicture[isscrew] = str(data['people'][num-1]['biophoto'])
                    crewmembercountry[isscrew] = str(data['people'][num-1]['country']).title()
                    if str(data['people'][num-1]['country'])==str('usa'):
                        crewmembercountry[isscrew] = str('USA')
                    isscrew = isscrew+1

            self.crew_screen.ids.crew1.text = str(crewmember[0])
            self.crew_screen.ids.crew1title.text = str(crewmembertitle[0])
            self.crew_screen.ids.crew1country.text = str(crewmembercountry[0])
            self.crew_screen.ids.crew1daysonISS.text = str(crewmemberdays[0])
            #self.crew_screen.ids.crew1image.source = str(crewmemberpicture[0])
            self.crew_screen.ids.crew2.text = str(crewmember[1])
            self.crew_screen.ids.crew2title.text = str(crewmembertitle[1])
            self.crew_screen.ids.crew2country.text = str(crewmembercountry[1])
            self.crew_screen.ids.crew2daysonISS.text = str(crewmemberdays[1])
            #self.crew_screen.ids.crew2image.source = str(crewmemberpicture[1])
            self.crew_screen.ids.crew3.text = str(crewmember[2])
            self.crew_screen.ids.crew3title.text = str(crewmembertitle[2])
            self.crew_screen.ids.crew3country.text = str(crewmembercountry[2])
            self.crew_screen.ids.crew3daysonISS.text = str(crewmemberdays[2])
            #self.crew_screen.ids.crew3image.source = str(crewmemberpicture[2])
            self.crew_screen.ids.crew4.text = str(crewmember[3])
            self.crew_screen.ids.crew4title.text = str(crewmembertitle[3])
            self.crew_screen.ids.crew4country.text = str(crewmembercountry[3])
            self.crew_screen.ids.crew4daysonISS.text = str(crewmemberdays[3])
            #self.crew_screen.ids.crew4image.source = str(crewmemberpicture[3])
            self.crew_screen.ids.crew5.text = str(crewmember[4])
            self.crew_screen.ids.crew5title.text = str(crewmembertitle[4])
            self.crew_screen.ids.crew5country.text = str(crewmembercountry[4])
            self.crew_screen.ids.crew5daysonISS.text = str(crewmemberdays[4])
            #self.crew_screen.ids.crew5image.source = str(crewmemberpicture[4])
            self.crew_screen.ids.crew6.text = str(crewmember[5])
            self.crew_screen.ids.crew6title.text = str(crewmembertitle[5])
            self.crew_screen.ids.crew6country.text = str(crewmembercountry[5])
            self.crew_screen.ids.crew6daysonISS.text = str(crewmemberdays[5])
            #self.crew_screen.ids.crew6image.source = str(crewmemberpicture[5])
            #self.crew_screen.ids.crew7.text = str(crewmember[6])
            #self.crew_screen.ids.crew7title.text = str(crewmembertitle[6])
            #self.crew_screen.ids.crew7country.text = str(crewmembercountry[6])
            #self.crew_screen.ids.crew7daysonISS.text = str(crewmemberdays[6])
            #self.crew_screen.ids.crew7image.source = str(crewmemberpicture[6])
            #self.crew_screen.ids.crew8.text = str(crewmember[7])
            #self.crew_screen.ids.crew8title.text = str(crewmembertitle[7])
            #self.crew_screen.ids.crew8country.text = str(crewmembercountry[7])
            #self.crew_screen.ids.crew8daysonISS.text = str(crewmemberdays[7])
            #self.crew_screen.ids.crew8image.source = str(crewmemberpicture[7]))
            #self.crew_screen.ids.crew9.text = str(crewmember[8])
            #self.crew_screen.ids.crew9title.text = str(crewmembertitle[8])
            #self.crew_screen.ids.crew9country.text = str(crewmembercountry[8])
            #self.crew_screen.ids.crew9daysonISS.text = str(crewmemberdays[8])
            #self.crew_screen.ids.crew9image.source = str(crewmemberpicture[8])
            #self.crew_screen.ids.crew10.text = str(crewmember[9])
            #self.crew_screen.ids.crew10title.text = str(crewmembertitle[9])
            #self.crew_screen.ids.crew10country.text = str(crewmembercountry[9])
            #self.crew_screen.ids.crew10daysonISS.text = str(crewmemberdays[9])
            #self.crew_screen.ids.crew10image.source = str(crewmemberpicture[9])
            #self.crew_screen.ids.crew11.text = str(crewmember[10])
            #self.crew_screen.ids.crew11title.text = str(crewmembertitle[10])
            #self.crew_screen.ids.crew11country.text = str(crewmembercountry[10])
            #self.crew_screen.ids.crew11daysonISS.text = str(crewmemberdays[10])
            #self.crew_screen.ids.crew11image.source = str(crewmemberpicture[10])
            #self.crew_screen.ids.crew12.text = str(crewmember[11])
            #self.crew_screen.ids.crew12title.text = str(crewmembertitle[11])
            #self.crew_screen.ids.crew12country.text = str(crewmembercountry[11])
            #self.crew_screen.ids.crew12daysonISS.text = str(crewmemberdays[11])
            #self.crew_screen.ids.crew12image.source = str(crewmemberpicture[11])

        def on_redirect(req, result):
            logWrite("Warning - checkCrew JSON failure (redirect)")
            logWrite(result)
            print(result)

        def on_failure(req, result):
            logWrite("Warning - checkCrew JSON failure (url failure)")

        def on_error(req, result):
            logWrite("Warning - checkCrew JSON failure (url error)")

        req = UrlRequest(iss_crew_url, on_success, on_redirect, on_failure, on_error, timeout=1)

    def map_rotation(self, args):
        scalefactor = 0.083333
        scaledValue = float(args)/scalefactor
        return scaledValue

    def map_psi_bar(self, args):
        scalefactor = 0.015
        scaledValue = (float(args)*scalefactor)+0.72
        return scaledValue

    def map_hold_bar(self, args):
        scalefactor = 0.0015
        scaledValue = (float(args)*scalefactor)+0.71
        return scaledValue

    def hold_timer(self, dt):
        global seconds2, holdstartTime
        logWrite("Function Call - hold timer")
        unixconvert = time.gmtime(time.time())
        currenthours = float(unixconvert[7])*24+unixconvert[3]+float(unixconvert[4])/60+float(unixconvert[5])/3600
        seconds2 = (currenthours-EVAstartTime)*3600
        seconds2 = int(seconds2)

        new_bar_x = self.map_hold_bar(260-seconds2)
        self.us_eva.ids.leak_timer.text = "~"+ str(int(seconds2)) + "s"
        self.us_eva.ids.Hold_bar.pos_hint = {"center_x": new_bar_x, "center_y": 0.49}
        self.us_eva.ids.Crewlock_Status_image.source = '/home/pi/Mimic/Pi/imgs/eva/LeakCheckLights.png'

    def signal_unsubscribed(self): #change images, used stale signal image
        global internet, ScreenList

        if not internet:
            for x in ScreenList:
                getattr(self, x).ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/offline.png'
            self.changeColors(0.5, 0.5, 0.5)
        else:
            for x in ScreenList:
                getattr(self, x).ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/SignalClientLost.png'
            self.changeColors(1, 0.5, 0)

        for x in ScreenList:
            getattr(self, x).ids.signal.size_hint_y = 0.112

    def signal_lost(self):
        global internet, ScreenList

        if not internet:
            for x in ScreenList:
                getattr(self, x).ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/offline.png'
            self.changeColors(0.5, 0.5, 0.5)
        else:
            for x in ScreenList:
                getattr(self, x).ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/signalred.zip'
            self.changeColors(1, 0, 0)

        for x in ScreenList:
            getattr(self, x).ids.signal.anim_delay = 0.4
        for x in ScreenList:
            getattr(self, x).ids.signal.size_hint_y = 0.112

    def signal_acquired(self):
        global internet, ScreenList

        if not internet:
            for x in ScreenList:
                getattr(self, x).ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/offline.png'
            self.changeColors(0.5, 0.5, 0.5)
        else:
            for x in ScreenList:
                getattr(self, x).ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/pulse-transparent.zip'
            self.changeColors(0, 1, 0)

        for x in ScreenList:
            getattr(self, x).ids.signal.anim_delay = 0.05
        for x in ScreenList:
            getattr(self, x).ids.signal.size_hint_y = 0.15

    def signal_stale(self):
        global internet, ScreenList

        if not internet:
            for x in ScreenList:
                getattr(self, x).ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/offline.png'
            self.changeColors(0.5, 0.5, 0.5)
        else:
            for x in ScreenList:
                getattr(self, x).ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/SignalOrangeGray.png'
            self.changeColors(1, 0.5, 0)

        for x in ScreenList:
            getattr(self, x).ids.signal.anim_delay = 0.12
        for x in ScreenList:
            getattr(self, x).ids.signal.size_hint_y = 0.112

    def signal_client_offline(self):
        global internet, ScreenList

        if not internet:
            for x in ScreenList:
                getattr(self, x).ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/offline.png'
            self.changeColors(0.5, 0.5, 0.5)
        else:
            for x in ScreenList:
                getattr(self, x).ids.signal.source = '/home/pi/Mimic/Pi/imgs/signal/SignalClientLost.png'
            self.changeColors(1, 0.5, 0)

        for x in ScreenList:
            getattr(self, x).ids.signal.anim_delay = 0.12
        for x in ScreenList:
            getattr(self, x).ids.signal.size_hint_y = 0.112

    def update_labels(self, dt): #THIS IS THE IMPORTANT FUNCTION
        global mimicbutton, switchtofake, demoboolean, runningDemo, fakeorbitboolean, psarj2, ssarj2, manualcontrol, aos, los, oldLOS, psarjmc, ssarjmc, ptrrjmc, strrjmc, beta1bmc, beta1amc, beta2bmc, beta2amc, beta3bmc, beta3amc, beta4bmc, beta4amc, US_EVAinProgress, position_x, position_y, position_z, velocity_x, velocity_y, velocity_z, altitude, velocity, iss_mass, testvalue, testfactor, airlock_pump, crewlockpres, leak_hold, firstcrossing, EVA_activities, repress, depress, oldAirlockPump, obtained_EVA_crew, EVAstartTime
        global holdstartTime, LS_Subscription
        global Disco, eva, standby, prebreath1, prebreath2, depress1, depress2, leakhold, repress
        global EPSstorageindex, channel1A_voltage, channel1B_voltage, channel2A_voltage, channel2B_voltage, channel3A_voltage, channel3B_voltage, channel4A_voltage, channel4B_voltage, USOS_Power
        global stationmode, sgant_elevation, sgant_xelevation
        global tdrs, module
        global old_mt_timestamp, old_mt_position, mt_speed

        arduino_count = len(SERIAL_PORTS)

        if arduino_count > 0:
            self.mimic_screen.ids.arduino_count.text = str(arduino_count)
            self.mimic_screen.ids.arduino.source = "/home/pi/Mimic/Pi/imgs/signal/arduino_notransmit.png"
            self.fakeorbit_screen.ids.arduino.source = "/home/pi/Mimic/Pi/imgs/signal/arduino_notransmit.png"
            self.fakeorbit_screen.ids.arduino_count.text = str(arduino_count)
        else:
            self.mimic_screen.ids.arduino_count.text = ""
            self.fakeorbit_screen.ids.arduino_count.text = ""
            self.mimic_screen.ids.arduino.source = "/home/pi/Mimic/Pi/imgs/signal/arduino_offline.png"
            self.fakeorbit_screen.ids.arduino.source = "/home/pi/Mimic/Pi/imgs/signal/arduino_offline.png"
            runningDemo = False

        if arduino_count > 0:
            self.mimic_screen.ids.mimicstartbutton.disabled = False
            self.fakeorbit_screen.ids.DemoStart.disabled = False
            self.fakeorbit_screen.ids.HTVDemoStart.disabled = False
            self.control_screen.ids.set90.disabled = False
            self.control_screen.ids.set0.disabled = False
            if mimicbutton:
                self.mimic_screen.ids.mimicstartbutton.disabled = True
                self.mimic_screen.ids.arduino.source = "/home/pi/Mimic/Pi/imgs/signal/Arduino_Transmit.zip"
            else:
                self.mimic_screen.ids.mimicstartbutton.disabled = False
        else:
            self.mimic_screen.ids.mimicstartbutton.disabled = True
            self.mimic_screen.ids.mimicstartbutton.text = "Transmit"
            self.fakeorbit_screen.ids.DemoStart.disabled = True
            self.fakeorbit_screen.ids.HTVDemoStart.disabled = True
            self.control_screen.ids.set90.disabled = True
            self.control_screen.ids.set0.disabled = True

        if runningDemo:
            self.fakeorbit_screen.ids.DemoStart.disabled = True
            self.fakeorbit_screen.ids.HTVDemoStart.disabled = True
            self.fakeorbit_screen.ids.DemoStop.disabled = False
            self.fakeorbit_screen.ids.HTVDemoStop.disabled = False
            self.fakeorbit_screen.ids.arduino.source = "/home/pi/Mimic/Pi/imgs/signal/Arduino_Transmit.zip"

        c.execute('select Value from telemetry')
        values = c.fetchall()
        c.execute('select Timestamp from telemetry')
        timestamps = c.fetchall()

        sub_status = str((values[255])[0]) #lightstreamer subscript checker
        client_status = str((values[256])[0]) #lightstreamer client checker

        psarj = "{:.2f}".format(float((values[0])[0]))
        if not switchtofake:
            psarj2 = float(psarj)
        if not manualcontrol:
            psarjmc = float(psarj)
        ssarj = "{:.2f}".format(float((values[1])[0]))
        if not switchtofake:
            ssarj2 = float(ssarj)
        if not manualcontrol:
            ssarjmc = float(ssarj)
        ptrrj = "{:.2f}".format(float((values[2])[0]))
        if not manualcontrol:
            ptrrjmc = float(ptrrj)
        strrj = "{:.2f}".format(float((values[3])[0]))
        if not manualcontrol:
            strrjmc = float(strrj)
        beta1b = "{:.2f}".format(float((values[4])[0]))
        if not switchtofake:
            beta1b2 = float(beta1b)
        if not manualcontrol:
            beta1bmc = float(beta1b)
        beta1a = "{:.2f}".format(float((values[5])[0]))
        if not switchtofake:
            beta1a2 = float(beta1a)
        if not manualcontrol:
            beta1amc = float(beta1a)
        beta2b = "{:.2f}".format(float((values[6])[0]))
        if not switchtofake:
            beta2b2 = float(beta2b) #+ 20.00
        if not manualcontrol:
            beta2bmc = float(beta2b)
        beta2a = "{:.2f}".format(float((values[7])[0]))
        if not switchtofake:
            beta2a2 = float(beta2a)
        if not manualcontrol:
            beta2amc = float(beta2a)
        beta3b = "{:.2f}".format(float((values[8])[0]))
        if not switchtofake:
            beta3b2 = float(beta3b)
        if not manualcontrol:
            beta3bmc = float(beta3b)
        beta3a = "{:.2f}".format(float((values[9])[0]))
        if not switchtofake:
            beta3a2 = float(beta3a)
        if not manualcontrol:
            beta3amc = float(beta3a)
        beta4b = "{:.2f}".format(float((values[10])[0]))
        if not switchtofake:
            beta4b2 = float(beta4b)
        if not manualcontrol:
            beta4bmc = float(beta4b)
        beta4a = "{:.2f}".format(float((values[11])[0]))
        if not switchtofake:
            beta4a2 = float(beta4a) #+ 20.00
        if not manualcontrol:
            beta4amc = float(beta4a)

        aos = "{:.2f}".format(int((values[12])[0]))
        los = "{:.2f}".format(int((values[13])[0]))
        sasa_el = "{:.2f}".format(float((values[14])[0]))
        active_sasa = int((values[54])[0])
        sasa1_active = int((values[53])[0])
        sasa2_active = int((values[52])[0])
        sgant_elevation = float((values[15])[0])
        sgant_xelevation = float((values[17])[0])
        sgant_transmit = float((values[41])[0])
        uhf1_power = int((values[233])[0]) #0 = off, 1 = on, 3 = failed
        uhf2_power = int((values[234])[0]) #0 = off, 1 = on, 3 = failed
        uhf_framesync = int((values[235])[0]) #1 or 0

        v1a = "{:.2f}".format(float((values[25])[0]))
        channel1A_voltage[EPSstorageindex] = float(v1a)
        v1b = "{:.2f}".format(float((values[26])[0]))
        channel1B_voltage[EPSstorageindex] = float(v1b)
        v2a = "{:.2f}".format(float((values[27])[0]))
        channel2A_voltage[EPSstorageindex] = float(v2a)
        v2b = "{:.2f}".format(float((values[28])[0]))
        channel2B_voltage[EPSstorageindex] = float(v2b)
        v3a = "{:.2f}".format(float((values[29])[0]))
        channel3A_voltage[EPSstorageindex] = float(v3a)
        v3b = "{:.2f}".format(float((values[30])[0]))
        channel3B_voltage[EPSstorageindex] = float(v3b)
        v4a = "{:.2f}".format(float((values[31])[0]))
        channel4A_voltage[EPSstorageindex] = float(v4a)
        v4b = "{:.2f}".format(float((values[32])[0]))
        channel4B_voltage[EPSstorageindex] = float(v4b)
        c1a = "{:.2f}".format(float((values[33])[0]))
        c1b = "{:.2f}".format(float((values[34])[0]))
        c2a = "{:.2f}".format(float((values[35])[0]))
        c2b = "{:.2f}".format(float((values[36])[0]))
        c3a = "{:.2f}".format(float((values[37])[0]))
        c3b = "{:.2f}".format(float((values[38])[0]))
        c4a = "{:.2f}".format(float((values[39])[0]))
        c4b = "{:.2f}".format(float((values[40])[0]))

        stationmode = float((values[46])[0]) #russian segment mode same as usos mode

        #GNC Telemetry
        rollerror = float((values[165])[0])
        pitcherror = float((values[166])[0])
        yawerror = float((values[167])[0])

        quaternion0 = float((values[171])[0])
        quaternion1 = float((values[172])[0])
        quaternion2 = float((values[173])[0])
        quaternion3 = float((values[174])[0])

        def dot(a,b):
            c = (a[0]*b[0])+(a[1]*b[1])+(a[2]*b[2])
            return c

        def cross(a,b):
            c = [a[1]*b[2] - a[2]*b[1],
                 a[2]*b[0] - a[0]*b[2],
                 a[0]*b[1] - a[1]*b[0]]
            return c

        iss_mass = "{:.2f}".format(float((values[48])[0]))

        #ISS state vectors
        position_x = float((values[55])[0]) #km
        position_y = float((values[56])[0]) #km
        position_z = float((values[57])[0]) #km
        velocity_x = float((values[58])[0])/1000.00 #convert to km/s
        velocity_y = float((values[59])[0])/1000.00 #convert to km/s
        velocity_z = float((values[60])[0])/1000.00 #convert to km/s

        #test values from orbital mechanics book
        #position_x = (-6045.00)
        #position_y = (-3490.00)
        #position_z = (2500.00)
        #velocity_x = (-3.457)
        #velocity_y = (6.618)
        #velocity_z = (2.533)

        pos_vec = [position_x, position_y, position_z]
        vel_vec = [velocity_x, velocity_y, velocity_z]

        altitude = "{:.2f}".format(math.sqrt(dot(pos_vec,pos_vec))-6371.00)
        velocity = "{:.2f}".format(math.sqrt(dot(vel_vec,vel_vec)))
        mu = 398600

        if float(altitude) > 0:
            pos_mag = math.sqrt(dot(pos_vec,pos_vec))
            vel_mag = math.sqrt(dot(vel_vec,vel_vec))

            v_radial = dot(vel_vec, pos_vec)/pos_mag

            h_mom = cross(pos_vec,vel_vec)
            h_mom_mag = math.sqrt(dot(h_mom,h_mom))

            inc = math.acos(h_mom[2]/h_mom_mag)
            self.orbit_data.ids.inc.text = "{:.2f}".format(math.degrees(inc))

            node_vec = cross([0,0,1],h_mom)
            node_mag = math.sqrt(dot(node_vec,node_vec))

            raan = math.acos(node_vec[0]/node_mag)
            if node_vec[1] < 0:
                raan = math.radians(360) - raan
            self.orbit_data.ids.raan.text = "{:.2f}".format(math.degrees(raan))

            pvnew = [x * (math.pow(vel_mag,2)-(mu/pos_mag)) for x in pos_vec]
            vvnew = [x * (pos_mag*v_radial) for x in vel_vec]
            e_vec1 = [(1/mu) * x for x in pvnew]
            e_vec2 = [(1/mu) * x for x in vvnew]
            e_vec = [e_vec1[0] - e_vec2[0],e_vec1[1] - e_vec2[1],e_vec1[2] - e_vec2[2] ]
            e_mag = math.sqrt(dot(e_vec,e_vec))
            self.orbit_data.ids.e.text = "{:.4f}".format(e_mag)

            arg_per = math.acos(dot(node_vec,e_vec)/(node_mag*e_mag))
            if e_vec[2] <= 0:
                arg_per = math.radians(360) - arg_per
            self.orbit_data.ids.arg_per.text = "{:.2f}".format(math.degrees(arg_per))

            ta = math.acos(dot(e_vec,pos_vec)/(e_mag*pos_mag))
            if v_radial <= 0:
                ta = math.radians(360) - ta
            self.orbit_data.ids.true_anomaly.text = "{:.2f}".format(math.degrees(ta))

            apogee = (math.pow(h_mom_mag,2)/mu)*(1/(1+e_mag*math.cos(math.radians(180))))
            perigee = (math.pow(h_mom_mag,2)/mu)*(1/(1+e_mag*math.cos(0)))
            apogee_height = apogee - 6371.00
            perigee_height = perigee - 6371.00
            sma = 0.5*(apogee+perigee) #km
            period = (2*math.pi/math.sqrt(mu))*math.pow(sma,3/2) #seconds

        cmg1_active = int((values[145])[0])
        cmg2_active = int((values[146])[0])
        cmg3_active = int((values[147])[0])
        cmg4_active = int((values[148])[0])
        numCMGs = int((values[149])[0])
        CMGtorqueRoll = float((values[150])[0])
        CMGtorquePitch = float((values[151])[0])
        CMGtorqueYaw = float((values[152])[0])
        CMGmomentum = float((values[153])[0])
        CMGmompercent = float((values[154])[0])
        CMGmomcapacity = float((values[175])[0])
        cmg1_spintemp = float((values[181])[0])
        cmg2_spintemp = float((values[182])[0])
        cmg3_spintemp = float((values[183])[0])
        cmg4_spintemp = float((values[184])[0])
        cmg1_halltemp = float((values[185])[0])
        cmg2_halltemp = float((values[186])[0])
        cmg3_halltemp = float((values[187])[0])
        cmg4_halltemp = float((values[188])[0])
        cmg1_vibration = float((values[237])[0])
        cmg2_vibration = float((values[238])[0])
        cmg3_vibration = float((values[239])[0])
        cmg4_vibration = float((values[240])[0])
        cmg1_motorcurrent = float((values[241])[0])
        cmg2_motorcurrent = float((values[242])[0])
        cmg3_motorcurrent = float((values[243])[0])
        cmg4_motorcurrent = float((values[244])[0])
        cmg1_wheelspeed = float((values[245])[0])
        cmg2_wheelspeed = float((values[246])[0])
        cmg3_wheelspeed = float((values[247])[0])
        cmg4_wheelspeed = float((values[248])[0])

        #EVA Telemetry
        airlock_pump_voltage = int((values[71])[0])
        airlock_pump_voltage_timestamp = float((timestamps[71])[0])
        airlock_pump_switch = int((values[72])[0])
        crewlockpres = float((values[16])[0])
        airlockpres = float((values[77])[0])

        #MSS Robotics Stuff
        mt_worksite = int((values[258])[0])
        self.mss_mt_screen.ids.mt_ws_value.text = str(mt_worksite)
        mt_position = float((values[257])[0])
        mt_position_timestamp = float((timestamps[257])[0])

        self.mss_mt_screen.ids.mt_position_value.text = str(mt_position)

        if (mt_position_timestamp - old_mt_timestamp) > 0:
            mt_speed = (mt_position - old_mt_position) / ((mt_position_timestamp - old_mt_timestamp)*3600)
            old_mt_timestamp = mt_position_timestamp
            old_mt_position = mt_position
        self.mss_mt_screen.ids.mt_speed_value.text = "{:2.2f}".format(float(mt_speed)) + " cm/s"


        ##US EPS Stuff---------------------------##
        solarbeta = "{:.2f}".format(float((values[176])[0]))

        power_1a = float(v1a) * float(c1a)
        power_1b = float(v1b) * float(c1b)
        power_2a = float(v2a) * float(c2a)
        power_2b = float(v2b) * float(c2b)
        power_3a = float(v3a) * float(c3a)
        power_3b = float(v3b) * float(c3b)
        power_4a = float(v4a) * float(c4a)
        power_4b = float(v4b) * float(c4b)

        USOS_Power = power_1a + power_1b + power_2a + power_2b + power_3a + power_3b + power_4a + power_4b
        self.eps_screen.ids.usos_power.text = str("{:.0f}".format(USOS_Power*-1.0)) + " W"
        self.eps_screen.ids.solarbeta.text = str(solarbeta)

        avg_total_voltage = (float(v1a)+float(v1b)+float(v2a)+float(v2b)+float(v3a)+float(v3b)+float(v4a)+float(v4b))/8.0

        avg_1a = (channel1A_voltage[0]+channel1A_voltage[1]+channel1A_voltage[2]+channel1A_voltage[3]+channel1A_voltage[4]+channel1A_voltage[5]+channel1A_voltage[6]+channel1A_voltage[7]+channel1A_voltage[8]+channel1A_voltage[9])/10
        avg_1b = (channel1B_voltage[0]+channel1B_voltage[1]+channel1B_voltage[2]+channel1B_voltage[3]+channel1B_voltage[4]+channel1B_voltage[5]+channel1B_voltage[6]+channel1B_voltage[7]+channel1B_voltage[8]+channel1B_voltage[9])/10
        avg_2a = (channel2A_voltage[0]+channel2A_voltage[1]+channel2A_voltage[2]+channel2A_voltage[3]+channel2A_voltage[4]+channel2A_voltage[5]+channel2A_voltage[6]+channel2A_voltage[7]+channel2A_voltage[8]+channel2A_voltage[9])/10
        avg_2b = (channel2B_voltage[0]+channel2B_voltage[1]+channel2B_voltage[2]+channel2B_voltage[3]+channel2B_voltage[4]+channel2B_voltage[5]+channel2B_voltage[6]+channel2B_voltage[7]+channel2B_voltage[8]+channel2B_voltage[9])/10
        avg_3a = (channel3A_voltage[0]+channel3A_voltage[1]+channel3A_voltage[2]+channel3A_voltage[3]+channel3A_voltage[4]+channel3A_voltage[5]+channel3A_voltage[6]+channel3A_voltage[7]+channel3A_voltage[8]+channel3A_voltage[9])/10
        avg_3b = (channel3B_voltage[0]+channel3B_voltage[1]+channel3B_voltage[2]+channel3B_voltage[3]+channel3B_voltage[4]+channel3B_voltage[5]+channel3B_voltage[6]+channel3B_voltage[7]+channel3B_voltage[8]+channel3B_voltage[9])/10
        avg_4a = (channel4A_voltage[0]+channel4A_voltage[1]+channel4A_voltage[2]+channel4A_voltage[3]+channel4A_voltage[4]+channel4A_voltage[5]+channel4A_voltage[6]+channel4A_voltage[7]+channel4A_voltage[8]+channel4A_voltage[9])/10
        avg_4b = (channel4B_voltage[0]+channel4B_voltage[1]+channel4B_voltage[2]+channel4B_voltage[3]+channel4B_voltage[4]+channel4B_voltage[5]+channel4B_voltage[6]+channel4B_voltage[7]+channel4B_voltage[8]+channel4B_voltage[9])/10
        halfavg_1a = (channel1A_voltage[0]+channel1A_voltage[1]+channel1A_voltage[2]+channel1A_voltage[3]+channel1A_voltage[4])/5
        halfavg_1b = (channel1B_voltage[0]+channel1B_voltage[1]+channel1B_voltage[2]+channel1B_voltage[3]+channel1B_voltage[4])/5
        halfavg_2a = (channel2A_voltage[0]+channel2A_voltage[1]+channel2A_voltage[2]+channel2A_voltage[3]+channel2A_voltage[4])/5
        halfavg_2b = (channel2B_voltage[0]+channel2B_voltage[1]+channel2B_voltage[2]+channel2B_voltage[3]+channel2B_voltage[4])/5
        halfavg_3a = (channel3A_voltage[0]+channel3A_voltage[1]+channel3A_voltage[2]+channel3A_voltage[3]+channel3A_voltage[4])/5
        halfavg_3b = (channel3B_voltage[0]+channel3B_voltage[1]+channel3B_voltage[2]+channel3B_voltage[3]+channel3B_voltage[4])/5
        halfavg_4a = (channel4A_voltage[0]+channel4A_voltage[1]+channel4A_voltage[2]+channel4A_voltage[3]+channel4A_voltage[4])/5
        halfavg_4b = (channel4B_voltage[0]+channel4B_voltage[1]+channel4B_voltage[2]+channel4B_voltage[3]+channel4B_voltage[4])/5

        EPSstorageindex += 1
        if EPSstorageindex > 9:
            EPSstorageindex = 0


        ## Station Mode ##

        if stationmode == 1.0:
            self.iss_screen.ids.stationmode_value.text = "Crew Rescue"
        elif stationmode == 2.0:
            self.iss_screen.ids.stationmode_value.text = "Survival"
        elif stationmode == 3.0:
            self.iss_screen.ids.stationmode_value.text = "Reboost"
        elif stationmode == 4.0:
            self.iss_screen.ids.stationmode_value.text = "Proximity Operations"
        elif stationmode == 5.0:
            self.iss_screen.ids.stationmode_value.text = "EVA"
        elif stationmode == 6.0:
            self.iss_screen.ids.stationmode_value.text = "Microgravity"
        elif stationmode == 7.0:
            self.iss_screen.ids.stationmode_value.text = "Standard"
        else:
            self.iss_screen.ids.stationmode_value.text = "n/a"

        ## ISS Potential Problems ##
        #ISS Leak - Check Pressure Levels
        #Number of CMGs online could reveal CMG failure
        #CMG speed less than 6600rpm
        #Solar arrays offline
        #Loss of attitude control, loss of cmg control
        #ISS altitude too low
        #Russion hook status - make sure all modules remain docked


        ##-------------------GNC Stuff---------------------------##

        roll = math.degrees(math.atan2(2.0 * (quaternion0 * quaternion1 + quaternion2 * quaternion3), 1.0 - 2.0 * (quaternion1 * quaternion1 + quaternion2 * quaternion2))) + rollerror
        pitch = math.degrees(math.asin(max(-1.0, min(1.0, 2.0 * (quaternion0 * quaternion2 - quaternion3 * quaternion1))))) + pitcherror
        yaw = math.degrees(math.atan2(2.0 * (quaternion0 * quaternion3 + quaternion1 * quaternion2), 1.0 - 2.0 * (quaternion2 * quaternion2 + quaternion3 * quaternion3))) + yawerror

        self.gnc_screen.ids.yaw.text = str("{:.2f}".format(yaw))
        self.gnc_screen.ids.pitch.text = str("{:.2f}".format(pitch))
        self.gnc_screen.ids.roll.text = str("{:.2f}".format(roll))

        self.gnc_screen.ids.cmgsaturation.value = CMGmompercent
        self.gnc_screen.ids.cmgsaturation_value.text = "CMG Saturation " + str("{:.1f}".format(CMGmompercent)) + "%"

        if cmg1_active == 1:
            self.gnc_screen.ids.cmg1.source = "/home/pi/Mimic/Pi/imgs/gnc/cmg.png"
        else:
            self.gnc_screen.ids.cmg1.source = "/home/pi/Mimic/Pi/imgs/gnc/cmg_offline.png"

        if cmg2_active == 1:
            self.gnc_screen.ids.cmg2.source = "/home/pi/Mimic/Pi/imgs/gnc/cmg.png"
        else:
            self.gnc_screen.ids.cmg2.source = "/home/pi/Mimic/Pi/imgs/gnc/cmg_offline.png"

        if cmg3_active == 1:
            self.gnc_screen.ids.cmg3.source = "/home/pi/Mimic/Pi/imgs/gnc/cmg.png"
        else:
            self.gnc_screen.ids.cmg3.source = "/home/pi/Mimic/Pi/imgs/gnc/cmg_offline.png"

        if cmg4_active == 1:
            self.gnc_screen.ids.cmg4.source = "/home/pi/Mimic/Pi/imgs/gnc/cmg.png"
        else:
            self.gnc_screen.ids.cmg4.source = "/home/pi/Mimic/Pi/imgs/gnc/cmg_offline.png"

        self.gnc_screen.ids.cmg1spintemp.text = "Spin Temp " + str("{:.1f}".format(cmg1_spintemp))
        self.gnc_screen.ids.cmg1halltemp.text = "Hall Temp " + str("{:.1f}".format(cmg1_halltemp))
        self.gnc_screen.ids.cmg1vibration.text = "Vibration " + str("{:.4f}".format(cmg1_vibration))
        self.gnc_screen.ids.cmg1current.text = "Current " + str("{:.1f}".format(cmg1_motorcurrent))
        self.gnc_screen.ids.cmg1speed.text = "Speed " + str("{:.1f}".format(cmg1_wheelspeed))

        self.gnc_screen.ids.cmg2spintemp.text = "Spin Temp " + str("{:.1f}".format(cmg2_spintemp))
        self.gnc_screen.ids.cmg2halltemp.text = "Hall Temp " + str("{:.1f}".format(cmg2_halltemp))
        self.gnc_screen.ids.cmg2vibration.text = "Vibration " + str("{:.4f}".format(cmg2_vibration))
        self.gnc_screen.ids.cmg2current.text = "Current " + str("{:.1f}".format(cmg2_motorcurrent))
        self.gnc_screen.ids.cmg2speed.text = "Speed " + str("{:.1f}".format(cmg2_wheelspeed))

        self.gnc_screen.ids.cmg3spintemp.text = "Spin Temp " + str("{:.1f}".format(cmg3_spintemp))
        self.gnc_screen.ids.cmg3halltemp.text = "Hall Temp " + str("{:.1f}".format(cmg3_halltemp))
        self.gnc_screen.ids.cmg3vibration.text = "Vibration " + str("{:.4f}".format(cmg3_vibration))
        self.gnc_screen.ids.cmg3current.text = "Current " + str("{:.1f}".format(cmg3_motorcurrent))
        self.gnc_screen.ids.cmg3speed.text = "Speed " + str("{:.1f}".format(cmg3_wheelspeed))

        self.gnc_screen.ids.cmg4spintemp.text = "Spin Temp " + str("{:.1f}".format(cmg4_spintemp))
        self.gnc_screen.ids.cmg4halltemp.text = "Hall Temp " + str("{:.1f}".format(cmg4_halltemp))
        self.gnc_screen.ids.cmg4vibration.text = "Vibration " + str("{:.4f}".format(cmg4_vibration))
        self.gnc_screen.ids.cmg4current.text = "Current " + str("{:.1f}".format(cmg4_motorcurrent))
        self.gnc_screen.ids.cmg4speed.text = "Speed " + str("{:.1f}".format(cmg4_wheelspeed))

        ##-------------------EPS Stuff---------------------------##

        #if halfavg_1a < 151.5: #discharging
        #    self.eps_screen.ids.array_1a.source = "/home/pi/Mimic/Pi/imgs/eps/array-discharging.zip"
        #    #self.eps_screen.ids.array_1a.color = 1, 1, 1, 0.8
        #elif avg_1a > 160.0: #charged
        #    self.eps_screen.ids.array_1a.source = "/home/pi/Mimic/Pi/imgs/eps/array-charged.zip"
        #elif halfavg_1a >= 151.5:  #charging
        #    self.eps_screen.ids.array_1a.source = "/home/pi/Mimic/Pi/imgs/eps/array-charging.zip"
        #    self.eps_screen.ids.array_1a.color = 1, 1, 1, 1.0
        #if float(c1a) > 0.0:    #power channel offline!
        #    self.eps_screen.ids.array_1a.source = "/home/pi/Mimic/Pi/imgs/eps/array-offline.png"

        #if halfavg_1b < 151.5: #discharging
        #    self.eps_screen.ids.array_1b.source = "/home/pi/Mimic/Pi/imgs/eps/array-discharging.zip"
        #    #self.eps_screen.ids.array_1b.color = 1, 1, 1, 0.8
        #elif avg_1b > 160.0: #charged
        #    self.eps_screen.ids.array_1b.source = "/home/pi/Mimic/Pi/imgs/eps/array-charged.zip"
        #elif halfavg_1b >= 151.5:  #charging
        #    self.eps_screen.ids.array_1b.source = "/home/pi/Mimic/Pi/imgs/eps/array-charging.zip"
        #    self.eps_screen.ids.array_1b.color = 1, 1, 1, 1.0
        #if float(c1b) > 0.0:                                  #power channel offline!
        #    self.eps_screen.ids.array_1b.source = "/home/pi/Mimic/Pi/imgs/eps/array-offline.png"

        #if halfavg_2a < 151.5: #discharging
        #    self.eps_screen.ids.array_2a.source = "/home/pi/Mimic/Pi/imgs/eps/array-discharging.zip"
        #    #self.eps_screen.ids.array_2a.color = 1, 1, 1, 0.8
        #elif avg_2a > 160.0: #charged
        #    self.eps_screen.ids.array_2a.source = "/home/pi/Mimic/Pi/imgs/eps/array-charged.zip"
        #elif halfavg_2a >= 151.5:  #charging
        #    self.eps_screen.ids.array_2a.source = "/home/pi/Mimic/Pi/imgs/eps/array-charging.zip"
        #    self.eps_screen.ids.array_2a.color = 1, 1, 1, 1.0
        #if float(c2a) > 0.0:                                  #power channel offline!
        #    self.eps_screen.ids.array_2a.source = "/home/pi/Mimic/Pi/imgs/eps/array-offline.png"

        #if halfavg_2b < 151.5: #discharging
        #    self.eps_screen.ids.array_2b.source = "/home/pi/Mimic/Pi/imgs/eps/array-discharging.zip"
        #    #self.eps_screen.ids.array_2b.color = 1, 1, 1, 0.8
        #elif avg_2b > 160.0: #charged
        #    self.eps_screen.ids.array_2b.source = "/home/pi/Mimic/Pi/imgs/eps/array-charged.zip"
        #elif halfavg_2b >= 151.5:  #charging
        #    self.eps_screen.ids.array_2b.source = "/home/pi/Mimic/Pi/imgs/eps/array-charging.zip"
        #    self.eps_screen.ids.array_2b.color = 1, 1, 1, 1.0
        #if float(c2b) > 0.0:                                  #power channel offline!
        #    self.eps_screen.ids.array_2b.source = "/home/pi/Mimic/Pi/imgs/eps/array-offline.png"

        #if halfavg_3a < 151.5: #discharging
        #    self.eps_screen.ids.array_3a.source = "/home/pi/Mimic/Pi/imgs/eps/array-discharging.zip"
            #self.eps_screen.ids.array_3a.color = 1, 1, 1, 0.8
        #elif avg_3a > 160.0: #charged
        #    self.eps_screen.ids.array_3a.source = "/home/pi/Mimic/Pi/imgs/eps/array-charged.zip"
        #elif halfavg_3a >= 151.5:  #charging
        #    self.eps_screen.ids.array_3a.source = "/home/pi/Mimic/Pi/imgs/eps/array-charging.zip"
        #    self.eps_screen.ids.array_3a.color = 1, 1, 1, 1.0
        #if float(c3a) > 0.0:                                  #power channel offline!
        #    self.eps_screen.ids.array_3a.source = "/home/pi/Mimic/Pi/imgs/eps/array-offline.png"

        #if halfavg_3b < 151.5: #discharging
        #    self.eps_screen.ids.array_3b.source = "/home/pi/Mimic/Pi/imgs/eps/array-discharging.zip"
            #self.eps_screen.ids.array_3b.color = 1, 1, 1, 0.8
        #elif avg_3b > 160.0: #charged
        #    self.eps_screen.ids.array_3b.source = "/home/pi/Mimic/Pi/imgs/eps/array-charged.zip"
        #elif halfavg_3b >= 151.5:  #charging
        #    self.eps_screen.ids.array_3b.source = "/home/pi/Mimic/Pi/imgs/eps/array-charging.zip"
        #    self.eps_screen.ids.array_3b.color = 1, 1, 1, 1.0
        #if float(c3b) > 0.0:                                  #power channel offline!
        #    self.eps_screen.ids.array_3b.source = "/home/pi/Mimic/Pi/imgs/eps/array-offline.png"

        #if halfavg_4a < 151.5: #discharging
        #    self.eps_screen.ids.array_4a.source = "/home/pi/Mimic/Pi/imgs/eps/array-discharging.zip"
        #    #self.eps_screen.ids.array_4a.color = 1, 1, 1, 0.8
        #elif avg_4a > 160.0: #charged
        #    self.eps_screen.ids.array_4a.source = "/home/pi/Mimic/Pi/imgs/eps/array-charged.zip"
        #elif halfavg_4a >= 151.5:  #charging
        #    self.eps_screen.ids.array_4a.source = "/home/pi/Mimic/Pi/imgs/eps/array-charging.zip"
        #    self.eps_screen.ids.array_4a.color = 1, 1, 1, 1.0
        #if float(c4a) > 0.0:                                  #power channel offline!
        #    self.eps_screen.ids.array_4a.source = "/home/pi/Mimic/Pi/imgs/eps/array-offline.png"

        #if halfavg_4b < 151.5: #discharging
        #    self.eps_screen.ids.array_4b.source = "/home/pi/Mimic/Pi/imgs/eps/array-discharging.zip"
        #    #self.eps_screen.ids.array_4b.color = 1, 1, 1, 0.8
        #elif avg_4b > 160.0: #charged
        #    self.eps_screen.ids.array_4b.source = "/home/pi/Mimic/Pi/imgs/eps/array-charged.zip"
        #elif halfavg_4b >= 151.5:  #charging
        #    self.eps_screen.ids.array_4b.source = "/home/pi/Mimic/Pi/imgs/eps/array-charging.zip"
        #    self.eps_screen.ids.array_4b.color = 1, 1, 1, 1.0
        #if float(c4b) > 0.0:                                  #power channel offline!
        #    self.eps_screen.ids.array_4b.source = "/home/pi/Mimic/Pi/imgs/eps/array-offline.png"
        #if avg_total_voltage > 151.5:
        #else:

        if float(v1a) >= 151.5 or float(v1b) >= 151.5 or float(v2a) >= 151.5 or float(v2b) >= 151.5 or float(v3a) >= 151.5 or float(v3b) >= 151.5 or float(v4a) >= 151.5 or float(v4b) >= 151.5:
            self.eps_screen.ids.eps_sun.color = 1, 1, 1, 1
        else:
            self.eps_screen.ids.eps_sun.color = 1, 1, 1, 0.1

        if float(v1a) < 151.5: #discharging
            self.eps_screen.ids.array_1a.source = "/home/pi/Mimic/Pi/imgs/eps/array-discharging.zip"
            #self.eps_screen.ids.array_1a.color = 1, 1, 1, 0.8
        elif float(v1a) > 160.0: #charged
            self.eps_screen.ids.array_1a.source = "/home/pi/Mimic/Pi/imgs/eps/array-charged.zip"
        elif float(v1a) >= 151.5:  #charging
            self.eps_screen.ids.array_1a.source = "/home/pi/Mimic/Pi/imgs/eps/array-charging.zip"
            self.eps_screen.ids.array_1a.color = 1, 1, 1, 1.0
        if float(c1a) > 0.0:    #power channel offline!
            self.eps_screen.ids.array_1a.source = "/home/pi/Mimic/Pi/imgs/eps/array-offline.png"

        if float(v1b) < 151.5: #discharging
            self.eps_screen.ids.array_1b.source = "/home/pi/Mimic/Pi/imgs/eps/array-discharging.zip"
            #self.eps_screen.ids.array_1b.color = 1, 1, 1, 0.8
        elif float(v1b) > 160.0: #charged
            self.eps_screen.ids.array_1b.source = "/home/pi/Mimic/Pi/imgs/eps/array-charged.zip"
        elif float(v1b) >= 151.5:  #charging
            self.eps_screen.ids.array_1b.source = "/home/pi/Mimic/Pi/imgs/eps/array-charging.zip"
            self.eps_screen.ids.array_1b.color = 1, 1, 1, 1.0
        if float(c1b) > 0.0:                                  #power channel offline!
            self.eps_screen.ids.array_1b.source = "/home/pi/Mimic/Pi/imgs/eps/array-offline.png"

        if float(v2a) < 151.5: #discharging
            self.eps_screen.ids.array_2a.source = "/home/pi/Mimic/Pi/imgs/eps/array-discharging.zip"
            #self.eps_screen.ids.array_2a.color = 1, 1, 1, 0.8
        elif float(v2a) > 160.0: #charged
            self.eps_screen.ids.array_2a.source = "/home/pi/Mimic/Pi/imgs/eps/array-charged.zip"
        elif float(v2a) >= 151.5:  #charging
            self.eps_screen.ids.array_2a.source = "/home/pi/Mimic/Pi/imgs/eps/array-charging.zip"
            self.eps_screen.ids.array_2a.color = 1, 1, 1, 1.0
        if float(c2a) > 0.0:                                  #power channel offline!
            self.eps_screen.ids.array_2a.source = "/home/pi/Mimic/Pi/imgs/eps/array-offline.png"

        if float(v2b) < 151.5: #discharging
            self.eps_screen.ids.array_2b.source = "/home/pi/Mimic/Pi/imgs/eps/array-discharging.zip"
            #self.eps_screen.ids.array_2b.color = 1, 1, 1, 0.8
        elif float(v2b) > 160.0: #charged
            self.eps_screen.ids.array_2b.source = "/home/pi/Mimic/Pi/imgs/eps/array-charged.zip"
        elif float(v2b) >= 151.5:  #charging
            self.eps_screen.ids.array_2b.source = "/home/pi/Mimic/Pi/imgs/eps/array-charging.zip"
            self.eps_screen.ids.array_2b.color = 1, 1, 1, 1.0
        if float(c2b) > 0.0:                                  #power channel offline!
            self.eps_screen.ids.array_2b.source = "/home/pi/Mimic/Pi/imgs/eps/array-offline.png"

        if float(v3a) < 151.5: #discharging
            self.eps_screen.ids.array_3a.source = "/home/pi/Mimic/Pi/imgs/eps/array-discharging.zip"
            #self.eps_screen.ids.array_3a.color = 1, 1, 1, 0.8
        elif float(v3a) > 160.0: #charged
            self.eps_screen.ids.array_3a.source = "/home/pi/Mimic/Pi/imgs/eps/array-charged.zip"
        elif float(v3a) >= 151.5:  #charging
            self.eps_screen.ids.array_3a.source = "/home/pi/Mimic/Pi/imgs/eps/array-charging.zip"
            self.eps_screen.ids.array_3a.color = 1, 1, 1, 1.0
        if float(c3a) > 0.0:                                  #power channel offline!
            self.eps_screen.ids.array_3a.source = "/home/pi/Mimic/Pi/imgs/eps/array-offline.png"

        if float(v3b) < 151.5: #discharging
            self.eps_screen.ids.array_3b.source = "/home/pi/Mimic/Pi/imgs/eps/array-discharging.zip"
            #self.eps_screen.ids.array_3b.color = 1, 1, 1, 0.8
        elif float(v3b) > 160.0: #charged
            self.eps_screen.ids.array_3b.source = "/home/pi/Mimic/Pi/imgs/eps/array-charged.zip"
        elif float(v3b) >= 151.5:  #charging
            self.eps_screen.ids.array_3b.source = "/home/pi/Mimic/Pi/imgs/eps/array-charging.zip"
            self.eps_screen.ids.array_3b.color = 1, 1, 1, 1.0
        if float(c3b) > 0.0:                                  #power channel offline!
            self.eps_screen.ids.array_3b.source = "/home/pi/Mimic/Pi/imgs/eps/array-offline.png"

        if float(v4a) < 151.5: #discharging
            self.eps_screen.ids.array_4a.source = "/home/pi/Mimic/Pi/imgs/eps/array-discharging.zip"
            #self.eps_screen.ids.array_4a.color = 1, 1, 1, 0.8
        elif float(v4a) > 160.0: #charged
            self.eps_screen.ids.array_4a.source = "/home/pi/Mimic/Pi/imgs/eps/array-charged.zip"
        elif float(v4a) >= 151.5:  #charging
            self.eps_screen.ids.array_4a.source = "/home/pi/Mimic/Pi/imgs/eps/array-charging.zip"
            self.eps_screen.ids.array_4a.color = 1, 1, 1, 1.0
        if float(c4a) > 0.0:                                  #power channel offline!
            self.eps_screen.ids.array_4a.source = "/home/pi/Mimic/Pi/imgs/eps/array-offline.png"
        #4b has a lower setpoint voltage for now - reverted back as of US EVA 63
        if float(v4b) < 141.5: #discharging
            self.eps_screen.ids.array_4b.source = "/home/pi/Mimic/Pi/imgs/eps/array-discharging.zip"
            #self.eps_screen.ids.array_4b.color = 1, 1, 1, 0.8
        elif float(v4b) > 150.0: #charged
            self.eps_screen.ids.array_4b.source = "/home/pi/Mimic/Pi/imgs/eps/array-charged.zip"
        elif float(v4b) >= 141.5:  #charging
            self.eps_screen.ids.array_4b.source = "/home/pi/Mimic/Pi/imgs/eps/array-charging.zip"
            self.eps_screen.ids.array_4b.color = 1, 1, 1, 1.0
        if float(c4b) > 0.0:                                  #power channel offline!
            self.eps_screen.ids.array_4b.source = "/home/pi/Mimic/Pi/imgs/eps/array-offline.png"

        ##-------------------C&T Functionality-------------------##
        self.ct_sgant_screen.ids.sgant_dish.angle = float(sgant_elevation)
        self.ct_sgant_screen.ids.sgant_elevation.text = "{:.2f}".format(float(sgant_elevation))

        #make sure radio animations turn off when no signal or no transmit
        if float(sgant_transmit) == 1.0 and float(aos) == 1.0:
            self.ct_sgant_screen.ids.radio_up.color = 1, 1, 1, 1
            if "10" in tdrs:
                self.ct_sgant_screen.ids.tdrs_west10.source = "/home/pi/Mimic/Pi/imgs/ct/TDRS.zip"
                self.ct_sgant_screen.ids.tdrs_west11.source = "/home/pi/Mimic/Pi/imgs/ct/TDRS.png"
                self.ct_sgant_screen.ids.tdrs_east12.source = "/home/pi/Mimic/Pi/imgs/ct/TDRS.png"
                self.ct_sgant_screen.ids.tdrs_east6.source = "/home/pi/Mimic/Pi/imgs/ct/TDRS.png"
                self.ct_sgant_screen.ids.tdrs_z7.source = "/home/pi/Mimic/Pi/imgs/ct/TDRS.png"
            if "11" in tdrs:
                self.ct_sgant_screen.ids.tdrs_west11.source = "/home/pi/Mimic/Pi/imgs/ct/TDRS.zip"
                self.ct_sgant_screen.ids.tdrs_west10.source = "/home/pi/Mimic/Pi/imgs/ct/TDRS.png"
                self.ct_sgant_screen.ids.tdrs_east12.source = "/home/pi/Mimic/Pi/imgs/ct/TDRS.png"
                self.ct_sgant_screen.ids.tdrs_east6.source = "/home/pi/Mimic/Pi/imgs/ct/TDRS.png"
                self.ct_sgant_screen.ids.tdrs_z7.source = "/home/pi/Mimic/Pi/imgs/ct/TDRS.png"
            if "12" in tdrs:
                self.ct_sgant_screen.ids.tdrs_west11.source = "/home/pi/Mimic/Pi/imgs/ct/TDRS.png"
                self.ct_sgant_screen.ids.tdrs_west10.source = "/home/pi/Mimic/Pi/imgs/ct/TDRS.png"
                self.ct_sgant_screen.ids.tdrs_east12.source = "/home/pi/Mimic/Pi/imgs/ct/TDRS.zip"
                self.ct_sgant_screen.ids.tdrs_east6.source = "/home/pi/Mimic/Pi/imgs/ct/TDRS.png"
                self.ct_sgant_screen.ids.tdrs_z7.source = "/home/pi/Mimic/Pi/imgs/ct/TDRS.png"
            if "6" in tdrs:
                self.ct_sgant_screen.ids.tdrs_west11.source = "/home/pi/Mimic/Pi/imgs/ct/TDRS.png"
                self.ct_sgant_screen.ids.tdrs_west10.source = "/home/pi/Mimic/Pi/imgs/ct/TDRS.png"
                self.ct_sgant_screen.ids.tdrs_east6.source = "/home/pi/Mimic/Pi/imgs/ct/TDRS.zip"
                self.ct_sgant_screen.ids.tdrs_east12.source = "/home/pi/Mimic/Pi/imgs/ct/TDRS.png"
                self.ct_sgant_screen.ids.tdrs_z7.source = "/home/pi/Mimic/Pi/imgs/ct/TDRS.png"
            if "7" in tdrs:
                self.ct_sgant_screen.ids.tdrs_west11.source = "/home/pi/Mimic/Pi/imgs/ct/TDRS.png"
                self.ct_sgant_screen.ids.tdrs_west10.source = "/home/pi/Mimic/Pi/imgs/ct/TDRS.png"
                self.ct_sgant_screen.ids.tdrs_east6.source = "/home/pi/Mimic/Pi/imgs/ct/TDRS.png"
                self.ct_sgant_screen.ids.tdrs_east12.source = "/home/pi/Mimic/Pi/imgs/ct/TDRS.png"
                self.ct_sgant_screen.ids.tdrs_z7.source = "/home/pi/Mimic/Pi/imgs/ct/TDRS.zip"

        elif float(aos) == 0.0 and (float(sgant_transmit) == 0.0 or float(sgant_transmit) == 1.0):
            self.ct_sgant_screen.ids.radio_up.color = 0, 0, 0, 0
            self.ct_sgant_screen.ids.tdrs_east12.source = "/home/pi/Mimic/Pi/imgs/ct/TDRS.png"
            self.ct_sgant_screen.ids.tdrs_east6.source = "/home/pi/Mimic/Pi/imgs/ct/TDRS.png"
            self.ct_sgant_screen.ids.tdrs_west11.source = "/home/pi/Mimic/Pi/imgs/ct/TDRS.png"
            self.ct_sgant_screen.ids.tdrs_west10.source = "/home/pi/Mimic/Pi/imgs/ct/TDRS.png"
            self.ct_sgant_screen.ids.tdrs_z7.source = "/home/pi/Mimic/Pi/imgs/ct/TDRS.png"

        #now check main CT screen radio signal
        if float(sgant_transmit) == 1.0 and float(aos) == 1.0:
            self.ct_screen.ids.sgant1_radio.color = 1, 1, 1, 1
            self.ct_screen.ids.sgant2_radio.color = 1, 1, 1, 1
        elif float(sgant_transmit) == 1.0 and float(aos) == 0.0:
            self.ct_screen.ids.sgant1_radio.color = 0, 0, 0, 0
            self.ct_screen.ids.sgant2_radio.color = 0, 0, 0, 0
        elif float(sgant_transmit) == 0.0:
            self.ct_screen.ids.sgant1_radio.color = 0, 0, 0, 0
            self.ct_screen.ids.sgant2_radio.color = 0, 0, 0, 0
        elif float(aos) == 0.0:
            self.ct_screen.ids.sgant1_radio.color = 0, 0, 0, 0
            self.ct_screen.ids.sgant2_radio.color = 0, 0, 0, 0

        if float(sasa1_active) == 1.0 and float(aos) == 1.0:
            self.ct_screen.ids.sasa1_radio.color = 1, 1, 1, 1
        elif float(sasa1_active) == 1.0 and float(aos) == 0.0:
            self.ct_screen.ids.sasa1_radio.color = 0, 0, 0, 0
        elif float(sasa1_active) == 0.0:
            self.ct_screen.ids.sasa1_radio.color = 0, 0, 0, 0
        elif float(aos) == 0.0:
            self.ct_screen.ids.sasa1_radio.color = 0, 0, 0, 0


        if float(sasa2_active) == 1.0 and float(aos) == 1.0:
            self.ct_screen.ids.sasa2_radio.color = 1, 1, 1, 1
        elif float(sasa2_active) == 1.0 and float(aos) == 0.0:
            self.ct_screen.ids.sasa2_radio.color = 0, 0, 0, 0
        elif float(sasa2_active) == 0.0:
            self.ct_screen.ids.sasa2_radio.color = 0, 0, 0, 0
        elif float(aos) == 0.0:
            self.ct_screen.ids.sasa2_radio.color = 0, 0, 0, 0

        if float(uhf1_power) == 1.0 and float(aos) == 1.0:
            self.ct_screen.ids.uhf1_radio.color = 1, 1, 1, 1
        elif float(uhf1_power) == 1.0 and float(aos) == 0.0:
            self.ct_screen.ids.uhf1_radio.color = 1, 0, 0, 1
        elif float(uhf1_power) == 0.0:
            self.ct_screen.ids.uhf1_radio.color = 0, 0, 0, 0

        if float(uhf2_power) == 1.0 and float(aos) == 1.0:
            self.ct_screen.ids.uhf2_radio.color = 1, 1, 1, 1
        elif float(uhf2_power) == 1.0 and float(aos) == 0.0:
            self.ct_screen.ids.uhf2_radio.color = 1, 0, 0, 1
        elif float(uhf2_power) == 0.0:
            self.ct_screen.ids.uhf2_radio.color = 0, 0, 0, 0

        ##-------------------EVA Functionality-------------------##
        if stationmode == 5:
            evaflashevent = Clock.schedule_once(self.flashEVAbutton, 1)

        ##-------------------US EVA Functionality-------------------##


        if airlock_pump_voltage == 1:
            self.us_eva.ids.pumpvoltage.text = "Airlock Pump Power On!"
            self.us_eva.ids.pumpvoltage.color = 0.33, 0.7, 0.18
        else:
            self.us_eva.ids.pumpvoltage.text = "Airlock Pump Power Off"
            self.us_eva.ids.pumpvoltage.color = 0, 0, 0

        if airlock_pump_switch == 1:
            self.us_eva.ids.pumpswitch.text = "Airlock Pump Active!"
            self.us_eva.ids.pumpswitch.color = 0.33, 0.7, 0.18
        else:
            self.us_eva.ids.pumpswitch.text = "Airlock Pump Inactive"
            self.us_eva.ids.pumpswitch.color = 0, 0, 0

        ##activate EVA button flash
        if (airlock_pump_voltage == 1 or crewlockpres < 734) and int(stationmode) == 5:
            usevaflashevent = Clock.schedule_once(self.flashUS_EVAbutton, 1)

        ##No EVA Currently
        if airlock_pump_voltage == 0 and airlock_pump_switch == 0 and crewlockpres > 740 and airlockpres > 740:
            eva = False
            self.us_eva.ids.leak_timer.text = ""
            self.us_eva.ids.Crewlock_Status_image.source = '/home/pi/Mimic/Pi/imgs/eva/BlankLights.png'
            self.us_eva.ids.EVA_occuring.color = 1, 0, 0
            self.us_eva.ids.EVA_occuring.text = "Currently No EVA"

        ##EVA Standby - NOT UNIQUE
        if airlock_pump_voltage == 1 and airlock_pump_switch == 1 and crewlockpres > 740 and airlockpres > 740 and int(stationmode) == 5:
            standby = True
            self.us_eva.ids.leak_timer.text = "~160s Leak Check"
            self.us_eva.ids.Crewlock_Status_image.source = '/home/pi/Mimic/Pi/imgs/eva/StandbyLights.png'
            self.us_eva.ids.EVA_occuring.color = 0, 0, 1
            self.us_eva.ids.EVA_occuring.text = "EVA Standby"
        else:
            standby = False

        ##EVA Prebreath Pressure
        if airlock_pump_voltage == 1 and crewlockpres > 740 and airlockpres > 740 and int(stationmode) == 5:
            prebreath1 = True
            self.us_eva.ids.Crewlock_Status_image.source = '/home/pi/Mimic/Pi/imgs/eva/PreBreatheLights.png'
            self.us_eva.ids.leak_timer.text = "~160s Leak Check"
            self.us_eva.ids.EVA_occuring.color = 0, 0, 1
            self.us_eva.ids.EVA_occuring.text = "Pre-EVA Nitrogen Purge"

        ##EVA Depress1
        if airlock_pump_voltage == 1 and airlock_pump_switch == 1 and crewlockpres < 740 and airlockpres > 740 and int(stationmode) == 5:
            depress1 = True
            self.us_eva.ids.leak_timer.text = "~160s Leak Check"
            self.us_eva.ids.EVA_occuring.text = "Crewlock Depressurizing"
            self.us_eva.ids.EVA_occuring.color = 0, 0, 1
            self.us_eva.ids.Crewlock_Status_image.source = '/home/pi/Mimic/Pi/imgs/eva/DepressLights.png'

        ##EVA Leakcheck
        if airlock_pump_voltage == 1 and crewlockpres < 260 and crewlockpres > 250 and (depress1 or leakhold) and int(stationmode) == 5:
            if depress1:
                holdstartTime = float(unixconvert[7])*24+unixconvert[3]+float(unixconvert[4])/60+float(unixconvert[5])/3600
            leakhold = True
            depress1 = False
            self.us_eva.ids.EVA_occuring.text = "Leak Check in Progress!"
            self.us_eva.ids.EVA_occuring.color = 0, 0, 1
            Clock.schedule_once(self.hold_timer, 1)
            self.us_eva.ids.Crewlock_Status_image.source = '/home/pi/Mimic/Pi/imgs/eva/LeakCheckLights.png'
        else:
            leakhold = False

        ##EVA Depress2
        if airlock_pump_voltage == 1 and crewlockpres <= 250 and crewlockpres > 3 and int(stationmode) == 5:
            leakhold = False
            self.us_eva.ids.leak_timer.text = "Complete"
            self.us_eva.ids.EVA_occuring.text = "Crewlock Depressurizing"
            self.us_eva.ids.EVA_occuring.color = 0, 0, 1
            self.us_eva.ids.Crewlock_Status_image.source = '/home/pi/Mimic/Pi/imgs/eva/DepressLights.png'

        ##EVA in progress
        if crewlockpres < 2.5 and int(stationmode) == 5:
            eva = True
            self.us_eva.ids.EVA_occuring.text = "EVA In Progress!!!"
            self.us_eva.ids.EVA_occuring.color = 0.33, 0.7, 0.18
            self.us_eva.ids.leak_timer.text = "Complete"
            self.us_eva.ids.Crewlock_Status_image.source = '/home/pi/Mimic/Pi/imgs/eva/InProgressLights.png'
            evatimerevent = Clock.schedule_once(self.EVA_clock, 1)

        ##Repress
        if airlock_pump_voltage == 0 and airlock_pump_switch == 0 and crewlockpres >= 3 and crewlockpres < 734 and int(stationmode) == 5:
            eva = False
            self.us_eva.ids.EVA_occuring.color = 0, 0, 1
            self.us_eva.ids.EVA_occuring.text = "Crewlock Repressurizing"
            self.us_eva.ids.Crewlock_Status_image.source = '/home/pi/Mimic/Pi/imgs/eva/RepressLights.png'

        ##-------------------RS EVA Functionality-------------------##
        ##if eva station mode and not us eva
        if airlock_pump_voltage == 0 and crewlockpres >= 734 and stationmode == 5:
            rsevaflashevent = Clock.schedule_once(self.flashRS_EVAbutton, 1)


        ##-------------------EVA Functionality End-------------------##

#        if (difference > -10) and (isinstance(App.get_running_app().root_window.children[0], Popup)==False):
#            LOSpopup = Popup(title='Loss of Signal', content=Label(text='Possible LOS Soon'), size_hint=(0.3, 0.2), auto_dismiss=True)
#            LOSpopup.open()

        ##-------------------Fake Orbit Simulator-------------------##
        self.fakeorbit_screen.ids.psarj.text = str(psarj)
        self.fakeorbit_screen.ids.ssarj.text = str(ssarj)
        self.fakeorbit_screen.ids.beta1a.text = str(beta1a)
        self.fakeorbit_screen.ids.beta1b.text = str(beta1b)
        self.fakeorbit_screen.ids.beta2a.text = str(beta2a)
        self.fakeorbit_screen.ids.beta2b.text = str(beta2b)
        self.fakeorbit_screen.ids.beta3a.text = str(beta3a)
        self.fakeorbit_screen.ids.beta3b.text = str(beta3b)
        self.fakeorbit_screen.ids.beta4a.text = str(beta4a)
        self.fakeorbit_screen.ids.beta4b.text = str(beta4b)

        if demoboolean:
            if Disco:
                serialWrite("Disco ")
                Disco = False
            serialWrite("PSARJ=" + psarj + " " + "SSARJ=" + ssarj + " " + "PTRRJ=" + ptrrj + " " + "STRRJ=" + strrj + " " + "B1B=" + beta1b + " " + "B1A=" + beta1a + " " + "B2B=" + beta2b + " " + "B2A=" + beta2a + " " + "B3B=" + beta3b + " " + "B3A=" + beta3a + " " + "B4B=" + beta4b + " " + "B4A=" + beta4a + " " + "V1A=" + v1a + " " + "V2A=" + v2a + " " + "V3A=" + v3a + " " + "V4A=" + v4a + " " + "V1B=" + v1b + " " + "V2B=" + v2b + " " + "V3B=" + v3b + " " + "V4B=" + v4b + " ")

        self.eps_screen.ids.psarj_value.text = psarj + "deg"
        self.eps_screen.ids.ssarj_value.text = ssarj + "deg"
        self.tcs_screen.ids.ptrrj_value.text = ptrrj + "deg"
        self.tcs_screen.ids.strrj_value.text = strrj + "deg"
        self.eps_screen.ids.beta1b_value.text = beta1b
        self.eps_screen.ids.beta1a_value.text = beta1a
        self.eps_screen.ids.beta2b_value.text = beta2b
        self.eps_screen.ids.beta2a_value.text = beta2a
        self.eps_screen.ids.beta3b_value.text = beta3b
        self.eps_screen.ids.beta3a_value.text = beta3a
        self.eps_screen.ids.beta4b_value.text = beta4b
        self.eps_screen.ids.beta4a_value.text = beta4a
        self.eps_screen.ids.c1a_value.text = c1a + "A"
        self.eps_screen.ids.v1a_value.text = v1a + "V"
        self.eps_screen.ids.c1b_value.text = c1b + "A"
        self.eps_screen.ids.v1b_value.text = v1b + "V"
        self.eps_screen.ids.c2a_value.text = c2a + "A"
        self.eps_screen.ids.v2a_value.text = v2a + "V"
        self.eps_screen.ids.c2b_value.text = c2b + "A"
        self.eps_screen.ids.v2b_value.text = v2b + "V"
        self.eps_screen.ids.c3a_value.text = c3a + "A"
        self.eps_screen.ids.v3a_value.text = v3a + "V"
        self.eps_screen.ids.c3b_value.text = c3b + "A"
        self.eps_screen.ids.v3b_value.text = v3b + "V"
        self.eps_screen.ids.c4a_value.text = c4a + "A"
        self.eps_screen.ids.v4a_value.text = v4a + "V"
        self.eps_screen.ids.c4b_value.text = c4b + "A"
        self.eps_screen.ids.v4b_value.text = v4b + "V"
        self.iss_screen.ids.altitude_value.text = str(altitude) + " km"
        self.iss_screen.ids.velocity_value.text = str(velocity) + " m/s"
        self.iss_screen.ids.stationmass_value.text = str(iss_mass) + " kg"

        self.us_eva.ids.EVA_needle.angle = float(self.map_rotation(0.0193368*float(crewlockpres)))
        self.us_eva.ids.crewlockpressure_value.text = "{:.2f}".format(0.0193368*float(crewlockpres))

        psi_bar_x = self.map_psi_bar(0.0193368*float(crewlockpres)) #convert to torr

        self.us_eva.ids.EVA_psi_bar.pos_hint = {"center_x": psi_bar_x, "center_y": 0.56}


        ##-------------------Signal Status Check-------------------##

        if client_status.split(":")[0] == "CONNECTED":
            if sub_status == "Subscribed":
                #client connected and subscibed to ISS telemetry
                if float(aos) == 1.00:
                    self.signal_acquired() #signal status 1 means acquired

                elif float(aos) == 0.00:
                    self.signal_lost() #signal status 0 means loss of signal

                elif float(aos) == 2.00:
                    self.signal_stale() #signal status 2 means data is not being updated from server
            else:
                self.signal_unsubscribed()
        else:
            self.signal_unsubscribed()

        if mimicbutton: # and float(aos) == 1.00):
            serialWrite("PSARJ=" + psarj + " " + "SSARJ=" + ssarj + " " + "PTRRJ=" + ptrrj + " " + "STRRJ=" + strrj + " " + "B1B=" + beta1b + " " + "B1A=" + beta1a + " " + "B2B=" + beta2b + " " + "B2A=" + beta2a + " " + "B3B=" + beta3b + " " + "B3A=" + beta3a + " " + "B4B=" + beta4b + " " + "B4A=" + beta4a + " " + "AOS=" + aos + " " + "V1A=" + v1a + " " + "V2A=" + v2a + " " + "V3A=" + v3a + " " + "V4A=" + v4a + " " + "V1B=" + v1b + " " + "V2B=" + v2b + " " + "V3B=" + v3b + " " + "V4B=" + v4b + " " + "ISS=" + module + " " + "Sgnt_el=" + str(int(sgant_elevation)) + " " + "Sgnt_xel=" + str(int(sgant_xelevation)) + " " + "Sgnt_xmit=" + str(int(sgant_transmit)) + " ")

#All GUI Screens are on separate kv files
Builder.load_file('/home/pi/Mimic/Pi/Screens/Settings_Screen.kv')
Builder.load_file('/home/pi/Mimic/Pi/Screens/FakeOrbitScreen.kv')
Builder.load_file('/home/pi/Mimic/Pi/Screens/Orbit_Screen.kv')
Builder.load_file('/home/pi/Mimic/Pi/Screens/Orbit_Pass.kv')
Builder.load_file('/home/pi/Mimic/Pi/Screens/Orbit_Data.kv')
Builder.load_file('/home/pi/Mimic/Pi/Screens/ISS_Screen.kv')
Builder.load_file('/home/pi/Mimic/Pi/Screens/ECLSS_Screen.kv')
Builder.load_file('/home/pi/Mimic/Pi/Screens/EPS_Screen.kv')
Builder.load_file('/home/pi/Mimic/Pi/Screens/CT_Screen.kv')
Builder.load_file('/home/pi/Mimic/Pi/Screens/CT_SGANT_Screen.kv')
Builder.load_file('/home/pi/Mimic/Pi/Screens/CT_SASA_Screen.kv')
Builder.load_file('/home/pi/Mimic/Pi/Screens/CT_UHF_Screen.kv')
Builder.load_file('/home/pi/Mimic/Pi/Screens/CT_Camera_Screen.kv')
Builder.load_file('/home/pi/Mimic/Pi/Screens/GNC_Screen.kv')
Builder.load_file('/home/pi/Mimic/Pi/Screens/TCS_Screen.kv')
Builder.load_file('/home/pi/Mimic/Pi/Screens/EVA_US_Screen.kv')
Builder.load_file('/home/pi/Mimic/Pi/Screens/EVA_RS_Screen.kv')
Builder.load_file('/home/pi/Mimic/Pi/Screens/EVA_Main_Screen.kv')
Builder.load_file('/home/pi/Mimic/Pi/Screens/EVA_Pictures.kv')
Builder.load_file('/home/pi/Mimic/Pi/Screens/Crew_Screen.kv')
Builder.load_file('/home/pi/Mimic/Pi/Screens/RS_Screen.kv')
Builder.load_file('/home/pi/Mimic/Pi/Screens/ManualControlScreen.kv')
Builder.load_file('/home/pi/Mimic/Pi/Screens/MSS_MT_Screen.kv')
Builder.load_file('/home/pi/Mimic/Pi/Screens/MimicScreen.kv')
Builder.load_file('/home/pi/Mimic/Pi/Screens/MainScreen.kv')

Builder.load_string('''
#:kivy 1.8
#:import kivy kivy
#:import win kivy.core.window
ScreenManager:
    Settings_Screen:
    FakeOrbitScreen:
    Orbit_Screen:
    Orbit_Pass:
    Orbit_Data:
    EPS_Screen:
    CT_Screen:
    CT_SASA_Screen:
    CT_UHF_Screen:
    CT_Camera_Screen:
    CT_SGANT_Screen:
    ISS_Screen:
    ECLSS_Screen:
    GNC_Screen:
    TCS_Screen:
    EVA_US_Screen:
    EVA_RS_Screen:
    EVA_Main_Screen:
    EVA_Pictures:
    RS_Screen:
    Crew_Screen:
    ManualControlScreen:
    MSS_MT_Screen:
    MimicScreen:
    MainScreen:
''')

if __name__ == '__main__':
    MainApp().run()
