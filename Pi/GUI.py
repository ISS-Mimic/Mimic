#!/usr/bin/python

import os # used to remove database on program exit; also used for importing config.json
os.environ["KIVY_NO_CONSOLELOG"] = "1"   # Kivy: no automatic console handler
os.environ["KIVY_LOG_LEVEL"]    = "error"  # (< INFO is ignored without handler,

from datetime import datetime, timedelta #used for time conversions and logging timestamps
from dateutil.relativedelta import relativedelta
import datetime as dtime #this is different from above for... reasons?
from subprocess import Popen #, PIPE, STDOUT #used to start/stop telemetry program and TDRS script and orbitmap
import threading, subprocess #used for background monitoring of USB ports for playback data
import time #used for time
import math #used for math
import glob #used to parse serial port names
import sqlite3 #used to access ISS telemetry database
import pytz #used for timezone conversion in orbit pass predictions
from bs4 import BeautifulSoup #used to parse webpages for data (EVA stats, ISS TLE)
import ephem #used for TLE orbit information on orbit screen
import serial #used to send data over serial to arduino
import json # used for serial port config and storing TLEs and crew info
from pyudev import Context, Devices, Monitor, MonitorObserver # for automatically detecting Arduinos - not available on Windows
import argparse
import sys
from collections import deque # used for storing russian data at init
import os.path as op #use for getting mimic directory
from pathlib import Path
import pathlib, sys, signal

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
from kivy.core.window import Window
from kivy.properties import ObjectProperty, BooleanProperty, StringProperty
from kivy.uix.screenmanager import ScreenManager, Screen, SwapTransition, NoTransition
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from functools import partial
from kivy.network.urlrequest import UrlRequest

#from screens import SCREEN_DEFS # import list of mimic screens
import database_initialize # create and populate database script
import Screens as screens
from utils.serial import serialWrite # custom Serial Write function
from utils.logger import log_info, log_error

mimic_data_directory = Path.home() / '.mimic_data'
mimic_directory = op.abspath(op.join(__file__, op.pardir, op.pardir, op.pardir))

print("Starting ISS Mimic Program")
print("Mimic Program Directory: " + mimic_directory + "/Mimic/Pi")
print("Mimic Data Directory: " + str(mimic_data_directory))

# Constants
SERIAL_SPEED = 9600

os.environ['KIVY_GL_BACKEND'] = 'gl' #need this to fix a kivy segfault that occurs with python3 for some reason

log_info("--------------------------------")
log_info("Initialized Mimic Program")

#-------------------------Look for an internet connection-----------------------------------

def probe_internet(callback, timeout=1.0) -> None:
    """
    Fire a single UrlRequest to `http://www.google.com/generate_204`.
    Calls `callback(bool_is_up)` on completion.
    """
    url = "http://www.google.com/generate_204"  # cheap 204 response

    def _done(req, *_):      # *_ swallows result / errors
        callback(True)

    def _fail(req, *_):
        callback(False)

    UrlRequest(url, on_success=_done, on_redirect=_done,
               on_failure=_fail, on_error=_fail,
               timeout=timeout)

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
            log_info(log_str)
            log_info(log_str)
    except ValueError:
        # Not printing anything because it sometimes tries too many times and is irrelevant
        pass

def add_tty_device(name_to_add):
    """ Adds tty device to list of serial ports after it successfully opens. """
    global SERIAL_PORTS, OPEN_SERIAL_PORTS
    if name_to_add not in SERIAL_PORTS:
        try:
            SERIAL_PORTS.append(name_to_add)
            OPEN_SERIAL_PORTS.append(serial.Serial(SERIAL_PORTS[-1], SERIAL_SPEED, write_timeout=0.5, timeout=0))
            log_str = "Added and opened %s." % name_to_add
            log_info(log_str)
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
    log_info("Skipping serial device:\n%s" % str(device))

def get_tty_dev_names(context):
    """ Checks ID_VENDOR string of tty devices to identify Arduinos. """
    names = []
    devices = context.list_devices(subsystem='tty')
    for d in devices:
        for k, v in d.items():
            # Check for both ID_VENDOR and ID_USB_VENDOR
            if k in ['ID_VENDOR', 'ID_USB_VENDOR']:
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
    serial_ports = list(set(serial_ports)) #remove duplicate ports that show up somehow
    return serial_ports

def open_serial_ports(serial_ports):
    """ Open all the serial ports in the list. Used when the GUI is first opened. """
    global OPEN_SERIAL_PORTS
    try:
        for s in serial_ports:
            OPEN_SERIAL_PORTS.append(serial.Serial(s, SERIAL_SPEED, write_timeout=0, timeout=0))
    except (OSError, serial.SerialException) as e:
        if USE_CONFIG_JSON:
            log_info("\nNot all serial ports were detected. Check config.json for accuracy.\n\n%s" % e)
        raise Exception(e)

context = Context()
if not USE_CONFIG_JSON:
    MONITOR = Monitor.from_netlink(context)
    TTY_OBSERVER = MonitorObserver(MONITOR, callback=detect_device_event, name='monitor-observer')
    TTY_OBSERVER.daemon = False
SERIAL_PORTS = get_serial_ports(context, USE_CONFIG_JSON)
OPEN_SERIAL_PORTS = []
open_serial_ports(SERIAL_PORTS)
log_str = "Serial ports opened: %s" % str(SERIAL_PORTS)
log_info(log_str)
if not USE_CONFIG_JSON:
    TTY_OBSERVER.start()
    log_str = "Started monitoring serial ports."
    log_info(log_str)
    log_info(log_str)

#-----------------------------Checking Databases-----------------------------------------
TDRSconn = sqlite3.connect('/dev/shm/tdrs.db')
TDRSconn.isolation_level = None
TDRScursor = TDRSconn.cursor()
VVconn = sqlite3.connect('/dev/shm/vv.db')
VVconn.isolation_level = None
VVcursor = VVconn.cursor()
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
playbackboolean = False
demoboolean = False
switchtofake = False
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
startingAnim = True
runningDemo = False
oldtdrs = "n/a"
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
old_mt_timestamp = 0.00
old_mt_position = 0.00

SCREEN_DEFS = {
    "main":            screens.MainScreen,
    "manualcontrol":   screens.ManualControlScreen,
    "led":             screens.LED_Screen,
    "playback":        screens.Playback_Screen,
    "settings":        screens.Settings_Screen,
    "mimic":           screens.MimicScreen,
    "iss":             screens.ISS_Screen,
    "cdh":             screens.CDH_Screen,
    "crew":            screens.Crew_Screen,
    "ct_camera":       screens.CT_Camera_Screen,
    "ct_sasa":         screens.CT_SASA_Screen,
    "ct_sgant":        screens.CT_SGANT_Screen,
    "ct":              screens.CT_Screen,
    "ct_uhf":          screens.CT_UHF_Screen,
    "iatcs":           screens.ECLSS_IATCS_Screen,
    "eclss":           screens.ECLSS_Screen,
    "wrm":             screens.ECLSS_WRM_Screen,
    "eps":             screens.EPS_Screen,
    "eva_emu":         screens.EVA_EMU_Screen,
    "eva_main":        screens.EVA_Main_Screen,
    "eva_pictures":    screens.EVA_Pictures,
    "ext_science":     screens.Science_EXT_Screen,
    "gnc":             screens.GNC_Screen,
    "int_science":     screens.Science_INT_Screen,
    "jef_science":     screens.Science_JEF_Screen,
    "mt":              screens.MSS_MT_Screen,
    "nral_science":    screens.Science_NRAL_Screen,
    "orbit_data":      screens.Orbit_Data,
    "orbit_pass":      screens.Orbit_Pass,
    "orbit":           screens.Orbit_Screen,
    "robo":            screens.Robo_Screen,
    "rs_dock":         screens.RS_Dock_Screen,
    "rs_eva":          screens.EVA_RS_Screen,
    "rs":              screens.RS_Screen,
    "science":         screens.Science_Screen,
    "spdm":            screens.SPDM_Screen,
    "ssrms":           screens.SSRMS_Screen,
    "tcs":             screens.TCS_Screen,
    "us_eva":          screens.EVA_US_Screen,
    "usos":            screens.USOS_Screen,
    "vv_image":        screens.VV_Image,
    "vv":              screens.VV_Screen,
}

class MainScreenManager(ScreenManager):
    mimic_directory = op.abspath(op.join(__file__, op.pardir, op.pardir, op.pardir))

class MainApp(App):
    mimic_directory = op.abspath(op.join(__file__, op.pardir, op.pardir, op.pardir))
    INTERNET_POLL_S = 1.0 # check internet connection every 1s
    manual_control = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.internet: bool | None = None # None = "unknown"
        self.ros_data = deque(maxlen=60)   # keep only the latest 60 samples
        # Manual Control variables
        self.manual_control: bool = False
        self.mc_angles: dict[str, float] = {         # default 0°
            k: 0.0 for k in (
                "beta1a","beta1b","beta2a","beta2b",
                "beta3a","beta3b","beta4a","beta4b",
                "psarj","ssarj","ptrrj","strrj"
            )
        }
        self.db_cursor = c        # <- assign existing cursor once
        # Process variables
        self.p = None
        self.p2 = None
        self.tty_observer = None

        self.mimic_directory = mimic_directory

    def build(self):
        # 1. instantiate once, store in a dict
        self.screens = {sid: cls(name=sid) for sid, cls in SCREEN_DEFS.items()}

        # 2. ScreenManager wiring
        root = MainScreenManager(transition=NoTransition())
        for scr in self.screens.values():
            root.add_widget(scr)
        root.current = "main"

        Clock.schedule_interval(self.update_labels, 1) #all telemetry wil refresh and get pushed to arduinos every half second!
        Clock.schedule_interval(self.animate3, 0.1)
        #Clock.schedule_interval(self.checkCrew, 600) #disabling for now issue #407
        #Clock.schedule_once(self.checkCrew, 30) #disabling for now issue #407
        Clock.schedule_once(self.updateVV, 10)

        Clock.schedule_interval(self._schedule_internet_probe,
                                self.INTERNET_POLL_S) # check for active internet connection

        Clock.schedule_interval(self.updateArduinoCount, 5)
        Clock.schedule_interval(self.updateVV, 500)
        Clock.schedule_interval(self.update_vv_values, 40)
        Clock.schedule_interval(self.updateNASAVVImage, 67)
        return root

    def _schedule_internet_probe(self, _dt) -> None:
        # Callbacks run async; keep lambda tiny.
        probe_internet(self._on_internet_result)

    def _on_internet_result(self, is_up: bool) -> None:
        if is_up == self.internet:
            return  # state unchanged ? nothing to do
        self.internet = is_up

        if is_up:
            self.signal_acquired()
        else:
            self.signal_client_offline()

    def updateVV(self, dt):
        proc = Popen(["python", mimic_directory + "/Mimic/Pi/VVcheck.py"])

    def updateArduinoCount(self, dt) -> None:
        """
        Refresh the little Arduino-status icon and counter on every screen
        that actually defines the two Image/Label widgets.
        
        - How it works now ----------------------------------------------
        Reads the global variables

        - Migration Path ----------------------------------------------
        1. when you create or update the serial port list elsewhere, also
            set self.serial_ports (e.g. in the hot plug handler)
        2. When the UI mimic button toggles, set self.mimicbutton
        3. Delete the global fall bals below
        """
        
        # ----------------------------------------------------------------
        # Phase-1 (works today): fall back to the old globals
        # ----------------------------------------------------------------

        arduino_count = (
            len(getattr(self, "serial_ports", []))
            if hasattr(self, "serial_ports")
            else len(SERIAL_PORTS)         # ? existing global
        )

        mimic_is_tx = (
            getattr(self, "mimicbutton", None)
            if hasattr(self, "mimicbutton")
            else mimicbutton               # ? existing global
        )

        """
        Refresh the Arduino-status icon & counter on screens that have them.
        """
        
        for scr in self.screens.values():
            ids = scr.ids

            # Skip screens without the widgets.
            if "arduino_count" not in ids or "arduino" not in ids:
                continue

            if arduino_count > 0:
                ids.arduino_count.text = str(arduino_count)
                ids.arduino.source = (
                    f"{self.mimic_directory}/Mimic/Pi/imgs/signal/"
                    + ("Arduino_Transmit.zip" if mimicbutton
                       else "arduino_notransmit.png")
                )
            else:
                ids.arduino_count.text = ""
                ids.arduino.source = (
                    f"{self.mimic_directory}/Mimic/Pi/imgs/signal/arduino_offline.png"
                )

        if arduino_count > 0:
            self.screens["mimic"].ids.mimicstartbutton.disabled = False
            self.screens["playback"].ids.DemoStart.disabled = False
            self.screens["playback"].ids.HTVDemoStart.disabled = False
            self.screens["playback"].ids.OFT2DemoStart.disabled = False
            self.screens["manualcontrol"].ids.set90.disabled = False
            self.screens["manualcontrol"].ids.set0.disabled = False
            if mimicbutton:
                self.screens["mimic"].ids.mimicstartbutton.disabled = True
            else:
                self.screens["mimic"].ids.mimicstartbutton.disabled = False
        else:
            self.screens["mimic"].ids.mimicstartbutton.disabled = True
            self.screens["mimic"].ids.mimicstartbutton.text = "Transmit"
            self.screens["playback"].ids.DemoStart.disabled = True
            self.screens["playback"].ids.HTVDemoStart.disabled = True
            self.screens["playback"].ids.OFT2DemoStart.disabled = True
            self.screens["manualcontrol"].ids.set90.disabled = True
            self.screens["manualcontrol"].ids.set0.disabled = True

    def deleteURLPictures(self, dt):
        log_info("Function call - deleteURLPictures")
        global EVA_picture_urls
        del EVA_picture_urls[:]
        EVA_picture_urls[:] = []

    def changePictures(self, dt):
        log_info("Function call - changeURLPictures")
        global EVA_picture_urls
        global urlindex
        urlsize = len(EVA_picture_urls)

        if urlsize > 0:
            self.screens["us_eva"].ids.EVAimage.source = EVA_picture_urls[urlindex]
            self.screens["eva_pictures"].ids.EVAimage.source = EVA_picture_urls[urlindex]

        urlindex = urlindex + 1
        if urlindex > urlsize-1:
            urlindex = 0

    def updateNASAVVImage(self, dt):
        self.screens["vv_image"].ids.VVimage.source = str(mimic_data_directory) + '/vv.png'
        self.screens["vv_image"].ids.VVimage.reload()
                
    def check_EVA_stats(self, lastname1, firstname1, lastname2, firstname2):
        global numEVAs1, EVAtime_hours1, EVAtime_minutes1, numEVAs2, EVAtime_hours2, EVAtime_minutes2
        log_info("Function call - check EVA stats")
        eva_url = 'http://www.spacefacts.de/eva/e_eva_az.htm'

        def on_success(req, result):
            log_info("Check EVA Stats - Successs")
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

            self.screens["us_eva"].ids.EV1.text = " (EV): " + str(firstname1) + " " + str(lastname1)
            self.screens["us_eva"].ids.EV2.text = " (EV): " + str(firstname2) + " " + str(lastname2)

            self.screens["us_eva"].ids.EV1_EVAnum.text = "Number of EVAs = " + str(EV1_EVA_number)
            self.screens["us_eva"].ids.EV2_EVAnum.text = "Number of EVAs = " + str(EV2_EVA_number)
            self.screens["us_eva"].ids.EV1_EVAtime.text = "Total EVA Time = " + str(EV1_hours) + "h " + str(EV1_minutes) + "m"
            self.screens["us_eva"].ids.EV2_EVAtime.text = "Total EVA Time = " + str(EV2_hours) + "h " + str(EV2_minutes) + "m"

        def on_redirect(req, result):
            log_info("Warning - EVA stats failure (redirect)")

        def on_failure(req, result):
            log_info("Warning - EVA stats failure (url failure)")

        def on_error(req, result):
            log_info("Warning - EVA stats failure (url error)")

        #obtain eva statistics web page for parsing
        req = UrlRequest(eva_url, on_success, on_redirect, on_failure, on_error, timeout=1)

    def checkBlogforEVA(self, dt):
        iss_blog_url =  'https://blogs.nasa.gov/spacestation/tag/spacewalk/'
        def on_success(req, data): #if blog data is successfully received, it is processed here
            log_info("Blog Success")
            soup = BeautifulSoup(data, "lxml")
            blog_entries = soup.find("div", {"class": "entry-content"})
            blog_text = blog_entries.get_text()

            iss_EVcrew_url = 'https://www.howmanypeopleareinspacerightnow.com/peopleinspace.json'

            def on_success2(req2, data2):
                log_info("Successfully fetched EV crew JSON")
                number_of_space = int(data2['number'])
                names = []
                for num in range(0, number_of_space):
                    names.append(str(data2['people'][num]['name']))

                try:
                    self.checkBlog(names,blog_text)
                except Exception as e:
                    log_error("Error checking blog: " + str(e))

            def on_redirect2(req, result):
                log_error("Warning - Get EVA crew failure (redirect)")
                log_error(result)

            def on_failure2(req, result):
                log_error("Warning - Get EVA crew failure (url failure)")

            def on_error2(req, result):
                log_error("Warning - Get EVA crew failure (url error)")

            req2 = UrlRequest(iss_EVcrew_url, on_success2, on_redirect2, on_failure2, on_error2, timeout=1)

        def on_redirect(req, result):
            log_error("Warning - Get nasa blog failure (redirect)")

        def on_failure(req, result):
            log_error("Warning - Get nasa blog failure (url failure)")

        def on_error(req, result):
            log_error("Warning - Get nasa blog failure (url error)")

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

        log_info("Likely EV1: "+ev1name)
        log_info("Likely EV2: "+ev2name)

        ev1_surname = ev1name.split()[-1]
        ev1_firstname = ev1name.split()[0]
        ev2_surname = ev2name.split()[-1]
        ev2_firstname = ev2name.split()[0]

        try:
            self.check_EVA_stats(ev1_surname,ev1_firstname,ev2_surname,ev2_firstname)
        except Exception as e:
            log_error("Error retrieving EVA stats: " + str(e))

    def flashROBObutton(self, instance):
        #log_info("Function call - flashRobo")

        self.screens["mimic"].ids.Robo_button.background_color = (0, 0, 1, 1)
        def reset_color(*args):
            self.screens["mimic"].ids.Robo_button.background_color = (1, 1, 1, 1)
        Clock.schedule_once(reset_color, 0.5)
    
    def flashUS_EVAbutton(self, instance):
        #log_info("Function call - flashUS_EVA")

        self.screens["eva_main"].ids.US_EVA_Button.background_color = (0, 0, 1, 1)
        def reset_color(*args):
            self.screens["eva_main"].ids.US_EVA_Button.background_color = (1, 1, 1, 1)
        Clock.schedule_once(reset_color, 0.5)

    def flashRS_EVAbutton(self, instance):
        #log_info("Function call - flashRS_EVA")

        self.screens["eva_main"].ids.RS_EVA_Button.background_color = (0, 0, 1, 1)
        def reset_color(*args):
            self.screens["eva_main"].ids.RS_EVA_Button.background_color = (1, 1, 1, 1)
        Clock.schedule_once(reset_color, 0.5)

    def flashEVAbutton(self, instance):
        #log_info("Function call - flashEVA")

        self.screens["mimic"].ids.EVA_button.background_color = (0, 0, 1, 1)
        def reset_color(*args):
            self.screens["mimic"].ids.EVA_button.background_color = (1, 1, 1, 1)
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

        self.screens["us_eva"].ids.EVA_clock.text =(str(hours) + ":" + str(minutes).zfill(2) + ":" + str(int(seconds)).zfill(2))
        self.screens["us_eva"].ids.EVA_clock.color = 0.33, 0.7, 0.18

    def animate(self, instance):
        global new_x2, new_y2
        self.screens["main"].ids.ISStiny2.size_hint = 0.07, 0.07
        new_x2 = new_x2+0.007
        new_y2 = (math.sin(new_x2*30)/18)+0.75
        if new_x2 > 1:
            new_x2 = new_x2-1.0
        self.screens["main"].ids.ISStiny2.pos_hint = {"center_x": new_x2, "center_y": new_y2}

    def animate3(self, instance):
        global new_x, new_y, sizeX, sizeY, startingAnim
        if new_x<0.886:
            new_x = new_x+0.007
            new_y = (math.sin(new_x*30)/18)+0.75
            self.screens["main"].ids.ISStiny.pos_hint = {"center_x": new_x, "center_y": new_y}
        else:
            if sizeX <= 0.15:
                sizeX = sizeX + 0.01
                sizeY = sizeY + 0.01
                self.screens["main"].ids.ISStiny.size_hint = sizeX, sizeY
            else:
                if startingAnim:
                    Clock.schedule_interval(self.animate, 0.1)
                    startingAnim = False

    def changeColors(self, r, g, b, *_) -> None:
        """
        Update the Kivy `signalcolor` property on every screen.

        Parameters
        ----------
        r, g, b : float
            Normalised RGB components (0-1) that the kv files bind to.
        *_      : any
            Extra positional args are ignored; they let the method still be
            scheduled by `Clock` if you pass `(dt,)`.
        """
        for scr in self.screens.values():
            scr.signalcolor = (r, g, b)

    def changeManualControlBoolean(self, *args):
        App.get_running_app().manual_control = args[0]


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
        log_info("Function Call - hold timer")
        unixconvert = time.gmtime(time.time())
        currenthours = float(unixconvert[7])*24+unixconvert[3]+float(unixconvert[4])/60+float(unixconvert[5])/3600
        seconds2 = (currenthours-EVAstartTime)*3600
        seconds2 = int(seconds2)

        new_bar_x = self.map_hold_bar(260-seconds2)
        self.screens["us_eva"].ids.leak_timer.text = "~"+ str(int(seconds2)) + "s"
        self.screens["us_eva"].ids.Hold_bar.pos_hint = {"center_x": new_bar_x, "center_y": 0.47}
        self.screens["us_eva"].ids.Crewlock_Status_image.source = mimic_directory + '/Mimic/Pi/imgs/eva/LeakCheckLights.png'

    def _broadcast_signal(self,
                          filename: str,
                          rgb: tuple[float, float, float],
                          anim_delay: float | None = None,
                          size_hint_y: float = 0.112) -> None:
        """
        Apply the same signal icon + colour to every screen.

        Parameters
        ----------
        filename      : just the file name, e.g. "offline.png"
        rgb           : (r, g, b) floats in 0-1 range
        anim_delay    : None ? leave current delay unchanged
        size_hint_y   : height of the Image widget
        """
        source_path = f"{self.mimic_directory}/Mimic/Pi/imgs/signal/{filename}"

        for scr in self.screens.values():
            sig = scr.ids.signal
            sig.source = source_path
            sig.size_hint_y = size_hint_y
            if anim_delay is not None:
                sig.anim_delay = anim_delay

        # update colour on every kv label bound to `signalcolor`
        self.changeColors(*rgb)

    def signal_unsubscribed(self):
        if not self.internet:
            self._broadcast_signal("offline.png", (0.5, 0.5, 0.5))
        else:
            self._broadcast_signal("SignalClientLost.png", (1, 0.5, 0))

    def signal_lost(self):
        if not self.internet:
            self._broadcast_signal("offline.png", (0.5, 0.5, 0.5))
        else:
            self._broadcast_signal("signalred.zip", (1, 0, 0), anim_delay=0.4)

    def signal_acquired(self):
        if not self.internet:
            self._broadcast_signal("offline.png", (0.5, 0.5, 0.5))
        else:
            self._broadcast_signal("pulse-transparent.zip", (0, 1, 0),
                                   anim_delay=0.05, size_hint_y=0.15)

    def signal_stale(self):
        if not self.internet:
            self._broadcast_signal("offline.png", (0.5, 0.5, 0.5))
        else:
            self._broadcast_signal("SignalOrangeGray.png", (1, 0.5, 0),
                                   anim_delay=0.12)

    def signal_client_offline(self):
        if not self.internet:
            self._broadcast_signal("offline.png", (0.5, 0.5, 0.5))
        else:
            self._broadcast_signal("SignalClientLost.png", (1, 0.5, 0),
                                   anim_delay=0.12)

    def update_vv_values(self, dt):
        try:
            # Check if the table exists before querying
            VVcursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vehicles'")
            if VVcursor.fetchone() is not None:
                VVcursor.execute('SELECT Mission FROM vehicles')
                mission = VVcursor.fetchall()
                VVcursor.execute('SELECT Type FROM vehicles')
                mission_type = VVcursor.fetchall()
                VVcursor.execute('SELECT Location FROM vehicles')
                location = VVcursor.fetchall()
                VVcursor.execute('SELECT Arrival FROM vehicles')
                arrival = VVcursor.fetchall()
                VVcursor.execute('SELECT Departure FROM vehicles')
                departure = VVcursor.fetchall()
                VVcursor.execute('SELECT Spacecraft FROM vehicles')
                spacecraft = VVcursor.fetchall()

                all_ports = {
                    "Node 2 Forward",
                    "Node 2 Zenith",
                    "Node 2 Nadir",
                    "Node 1 Nadir",
                    "Service Module Aft",
                    "MRM-2 Zenith",
                    "MRM-1 Nadir",
                    "RS Node Nadir"
                }

                occupied_ports = set()

                for i, port in enumerate(location):
                    port = port[0]  # Extract the port name from the tuple
                    occupied_ports.add(port)
                    sc_check = spacecraft[i][0].strip()
                    sc_check = spacecraft[i][0].replace('\xa0', ' ')  # Replace non-breaking space with a regular space

                    if "SC" in sc_check or "Boeing" in sc_check or "CST" in sc_check:
                        sc_name = "CST-100 Starliner"
                        sc_name2 = sc_check
                    elif "Crew" in sc_check:
                        sc_name = "Crew Dragon"
                        sc_name2 = sc_check.replace(sc_name + " ", "").strip()
                    elif "Cargo" in sc_check:
                        sc_name = "Cargo Dragon"
                        sc_name2 = sc_check.replace(sc_name+" ","")
                    elif "Soyuz" in sc_check:
                        sc_name = "Soyuz MS"
                        sc_name2 = sc_check.replace(sc_name+" ","")
                    elif "Progress" in sc_check:
                        sc_name = "Progress MS"
                        sc_name2 = sc_check.replace(sc_name+" ","")
                    elif "NG" in mission[i][0]:
                        sc_name = "Cygnus"
                        sc_name2 = sc_check
                    else:
                        sc_name = "n/a"
                        sc_name2 = "n/a"

                    if arrival[i][0] is None:
                        arrival_date = "n/a"
                    else:
                        arrival_date = str(arrival[i][0])[:10]
                    
                    if departure[i][0] is None:
                        departure_date = "n/a"
                    else:
                        departure_date = str(departure[i][0])[:10]

                    if str(mission_type[i][0]) == "Crewed":
                        type_edit = " (Crewed)"
                    else:
                        type_edit = " (Cargo)"

                    if port == "Node 2 Forward":
                        self.screens["usos"].ids.n2f_mission.text = str(mission[i][0]) + type_edit
                        self.screens["usos"].ids.n2f_vehicle.text = sc_name
                        self.screens["usos"].ids.n2f_spacecraft.text = sc_name2
                        self.screens["usos"].ids.n2f_arrival.text = "Arrival: " + arrival_date
                        self.screens["usos"].ids.n2f_departure.text = "Departure: " + departure_date
                        self.screens["usos"].ids.n2f_label.text = sc_name + "\n" + str(mission[i][0])
                        self.screens["vv"].ids.n2f_label.text = sc_name + "\n" + str(mission[i][0])
                        if "Dragon" in sc_name:
                            self.screens["usos"].ids.n2f_dragon.opacity = 1.0
                            self.screens["usos"].ids.n2f_starliner.opacity = 0.0
                            self.screens["vv"].ids.n2f_dragon.opacity = 1.0
                            self.screens["vv"].ids.n2f_starliner.opacity = 0.0
                        elif sc_name == "CST-100 Starliner":
                            self.screens["usos"].ids.n2f_starliner.opacity = 1.0
                            self.screens["usos"].ids.n2f_dragon.opacity = 0.0
                            self.screens["vv"].ids.n2f_dragon.opacity = 0.0
                            self.screens["vv"].ids.n2f_starliner.opacity = 1.0
                    elif port == "Node 2 Zenith":
                        self.screens["usos"].ids.n2z_mission.text = str(mission[i][0]) + type_edit
                        self.screens["usos"].ids.n2z_vehicle.text = sc_name
                        self.screens["usos"].ids.n2z_spacecraft.text = sc_name2
                        self.screens["usos"].ids.n2z_arrival.text = "Arrival: " + arrival_date
                        self.screens["usos"].ids.n2z_departure.text = "Departure: " + departure_date
                        self.screens["usos"].ids.n2z_label.text = sc_name + "\n" + str(mission[i][0])
                        self.screens["vv"].ids.n2z_label.text = sc_name + "\n" + str(mission[i][0])
                        if "Dragon" in sc_name:
                            self.screens["usos"].ids.n2z_dragon.opacity = 1.0
                            self.screens["usos"].ids.n2z_starliner.opacity = 0.0
                            self.screens["vv"].ids.n2z_dragon.opacity = 1.0
                            self.screens["vv"].ids.n2z_starliner.opacity = 0.0
                        elif sc_name == "CST-100 Starliner":
                            self.screens["usos"].ids.n2z_starliner.opacity = 1.0
                            self.screens["usos"].ids.n2z_dragon.opacity = 0.0
                            self.screens["vv"].ids.n2z_dragon.opacity = 0.0
                            self.screens["vv"].ids.n2z_starliner.opacity = 1.0
                    elif port == "Node 2 Nadir":
                        self.screens["usos"].ids.n2n_mission.text = str(mission[i][0]) + type_edit
                        self.screens["usos"].ids.n2n_vehicle.text = sc_name
                        self.screens["usos"].ids.n2n_spacecraft.text = sc_name2
                        self.screens["usos"].ids.n2n_arrival.text = "Arrival: " + arrival_date
                        self.screens["usos"].ids.n2n_departure.text = "Departure: " + departure_date
                        self.screens["usos"].ids.n2n_label.text = sc_name + "\n" + str(mission[i][0])
                        self.screens["vv"].ids.n2n_label.text = sc_name + "\n" + str(mission[i][0])
                        #if "Dream" in sc_name:
                            #self.screens["usos"].ids.n2n_dreamchaser.opacity = 1.0
                            #self.screens["usos"].ids.n2n_htvx.opacity = 0.0
                            #self.screens["vv"].ids.n2n_dreamchaser.opacity = 1.0
                            #self.screens["vv"].ids.n2n_htvx.opacity = 0.0
                        #elif "HTV" in sc_name:
                            #self.screens["usos"].ids.n2n_dreamchaser.opacity = 0.0
                            #self.screens["usos"].ids.n2n_htvx.opacity = 1.0
                            #self.screens["vv"].ids.n2n_dreamchaser.opacity = 0.0
                            #self.screens["vv"].ids.n2n_htvx.opacity = 1.0
                    elif port == "Node 1 Nadir":
                        self.screens["usos"].ids.n1n_mission.text = str(mission[i][0]) + type_edit
                        self.screens["usos"].ids.n1n_vehicle.text = sc_name
                        self.screens["usos"].ids.n1n_spacecraft.text = sc_name2
                        self.screens["usos"].ids.n1n_arrival.text = "Arrival: " + arrival_date
                        self.screens["usos"].ids.n1n_departure.text = "Departure: " + departure_date
                        self.screens["usos"].ids.n1n_label.text = sc_name + "\n" + str(mission[i][0])
                        self.screens["vv"].ids.n1n_label.text = sc_name + "\n" + str(mission[i][0])
                        if sc_name == "Cygnus":
                            self.screens["usos"].ids.n1n_cygnus.opacity = 1.0
                            self.screens["vv"].ids.n1n_cygnus.opacity = 1.0
                        else:
                            self.screens["usos"].ids.n1n_cygnus.opacity = 0.0
                            self.screens["vv"].ids.n1n_cygnus.opacity = 0.0
                    elif port == "Service Module Aft":
                        self.screens["rs"].ids.sma_mission.text = str(mission[i][0]) + type_edit
                        self.screens["rs"].ids.sma_vehicle.text = sc_name
                        self.screens["rs"].ids.sma_spacecraft.text = sc_name2
                        self.screens["rs"].ids.sma_arrival.text = "Arrival: " + arrival_date
                        self.screens["rs"].ids.sma_departure.text = "Departure: " + departure_date
                        self.screens["rs"].ids.sma_label.text = sc_name + "\n" + str(mission[i][0])
                        self.screens["vv"].ids.sma_label.text = sc_name + "\n" + str(mission[i][0])
                        if "Soyuz" in sc_name:
                            self.screens["rs"].ids.sma_soyuz.opacity = 1.0
                            self.screens["rs"].ids.sma_progress.opacity = 0.0
                            self.screens["vv"].ids.sma_soyuz.opacity = 1.0
                            self.screens["vv"].ids.sma_progress.opacity = 0.0
                        elif "Progress" in sc_name:
                            self.screens["rs"].ids.sma_soyuz.opacity = 0.0
                            self.screens["rs"].ids.sma_progress.opacity = 1.0
                            self.screens["vv"].ids.sma_soyuz.opacity = 0.0
                            self.screens["vv"].ids.sma_progress.opacity = 1.0
                    elif port == "MRM-2 Zenith":
                        self.screens["rs"].ids.mrm2_mission.text = str(mission[i][0]) + type_edit
                        self.screens["rs"].ids.mrm2_vehicle.text = sc_name
                        self.screens["rs"].ids.mrm2_spacecraft.text = sc_name2
                        self.screens["rs"].ids.mrm2_arrival.text = "Arrival: " + arrival_date
                        self.screens["rs"].ids.mrm2_departure.text = "Departure: " + departure_date
                        self.screens["rs"].ids.mrm2_label.text = sc_name + "\n" + str(mission[i][0])
                        self.screens["vv"].ids.mrm2_label.text = sc_name + "\n" + str(mission[i][0])
                        if "Soyuz" in sc_name:
                            self.screens["rs"].ids.mrm2_soyuz.opacity = 1.0
                            self.screens["rs"].ids.mrm2_progress.opacity = 0.0
                            self.screens["vv"].ids.mrm2_soyuz.opacity = 1.0
                            self.screens["vv"].ids.mrm2_progress.opacity = 0.0
                        elif "Progress" in sc_name:
                            self.screens["rs"].ids.mrm2_soyuz.opacity = 0.0
                            self.screens["rs"].ids.mrm2_progress.opacity = 1.0
                            self.screens["vv"].ids.mrm2_soyuz.opacity = 0.0
                            self.screens["vv"].ids.mrm2_progress.opacity = 1.0
                    elif port == "MRM-1 Nadir":
                        self.screens["rs"].ids.mrm1_mission.text = str(mission[i][0]) + type_edit
                        self.screens["rs"].ids.mrm1_vehicle.text = sc_name
                        self.screens["rs"].ids.mrm1_spacecraft.text = sc_name2
                        self.screens["rs"].ids.mrm1_arrival.text = "Arrival: " + arrival_date
                        self.screens["rs"].ids.mrm1_departure.text = "Departure: " + departure_date
                        self.screens["rs"].ids.mrm1_label.text = sc_name + "\n" + str(mission[i][0])
                        self.screens["vv"].ids.mrm1_label.text = sc_name + "\n" + str(mission[i][0])
                        if "Soyuz" in sc_name:
                            self.screens["rs"].ids.mrm1_soyuz.opacity = 1.0
                            self.screens["rs"].ids.mrm1_progress.opacity = 0.0
                            self.screens["vv"].ids.mrm1_soyuz.opacity = 1.0
                            self.screens["vv"].ids.mrm1_progress.opacity = 0.0
                        elif "Progress" in sc_name:
                            self.screens["rs"].ids.mrm1_soyuz.opacity = 0.0
                            self.screens["rs"].ids.mrm1_progress.opacity = 1.0
                            self.screens["vv"].ids.mrm1_soyuz.opacity = 0.0
                            self.screens["vv"].ids.mrm1_progress.opacity = 1.0
                    elif port == "RS Node Nadir":
                        self.screens["rs"].ids.rsn_mission.text = str(mission[i][0]) + type_edit
                        self.screens["rs"].ids.rsn_vehicle.text = sc_name
                        self.screens["rs"].ids.rsn_spacecraft.text = sc_name2
                        self.screens["rs"].ids.rsn_arrival.text = "Arrival: " + arrival_date
                        self.screens["rs"].ids.rsn_departure.text = "Departure: " + departure_date
                        self.screens["rs"].ids.rsn_label.text = sc_name + "\n" + str(mission[i][0])
                        self.screens["vv"].ids.rsn_label.text = sc_name + "\n" + str(mission[i][0])
                        if "Soyuz" in sc_name:
                            self.screens["rs"].ids.rsn_soyuz.opacity = 1.0
                            self.screens["rs"].ids.rsn_progress.opacity = 0.0
                            self.screens["vv"].ids.rsn_soyuz.opacity = 1.0
                            self.screens["vv"].ids.rsn_progress.opacity = 0.0
                        elif "Progress" in sc_name:
                            self.screens["rs"].ids.rsn_soyuz.opacity = 0.0
                            self.screens["rs"].ids.rsn_progress.opacity = 1.0
                            self.screens["vv"].ids.rsn_soyuz.opacity = 0.0
                            self.screens["vv"].ids.rsn_progress.opacity = 1.0

                unoccupied_ports = all_ports - occupied_ports

                # Handle unoccupied ports
                for port in unoccupied_ports:
                    if port == "Node 2 Forward":
                        self.screens["usos"].ids.n2f_mission.text = "-"
                        self.screens["usos"].ids.n2f_vehicle.text = "-"
                        self.screens["usos"].ids.n2f_spacecraft.text = "-"
                        self.screens["usos"].ids.n2f_arrival.text = "-"
                        self.screens["usos"].ids.n2f_departure.text = "-"
                        self.screens["usos"].ids.n2f_dragon.opacity = 0.0
                        self.screens["usos"].ids.n2f_starliner.opacity = 0.0
                        self.screens["usos"].ids.n2f_label.text = ""
                        self.screens["vv"].ids.n2f_label.text = ""
                        self.screens["vv"].ids.n2f_dragon.opacity = 0.0
                        self.screens["vv"].ids.n2f_starliner.opacity = 0.0
                    elif port == "Node 2 Zenith":
                        self.screens["usos"].ids.n2z_mission.text = "-"
                        self.screens["usos"].ids.n2z_vehicle.text = "-"
                        self.screens["usos"].ids.n2z_spacecraft.text = "-"
                        self.screens["usos"].ids.n2z_arrival.text = "-"
                        self.screens["usos"].ids.n2z_departure.text = "-"
                        self.screens["usos"].ids.n2z_dragon.opacity = 0.0
                        self.screens["usos"].ids.n2z_starliner.opacity = 0.0
                        self.screens["usos"].ids.n2z_label.text = ""
                        self.screens["vv"].ids.n2z_label.text = ""
                        self.screens["vv"].ids.n2z_dragon.opacity = 0.0
                        self.screens["vv"].ids.n2z_starliner.opacity = 0.0
                    elif port == "Node 2 Nadir":
                        self.screens["usos"].ids.n2n_mission.text = "-"
                        self.screens["usos"].ids.n2n_vehicle.text = "-"
                        self.screens["usos"].ids.n2n_spacecraft.text = "-"
                        self.screens["usos"].ids.n2n_arrival.text = "-"
                        self.screens["usos"].ids.n2n_departure.text = "-"
                        self.screens["usos"].ids.n2n_label.text = ""
                        self.screens["vv"].ids.n2n_label.text = ""
                    elif port == "Node 1 Nadir":
                        self.screens["usos"].ids.n1n_mission.text = "-"
                        self.screens["usos"].ids.n1n_vehicle.text = "-"
                        self.screens["usos"].ids.n1n_spacecraft.text = "-"
                        self.screens["usos"].ids.n1n_arrival.text = "-"
                        self.screens["usos"].ids.n1n_departure.text = "-"
                        self.screens["usos"].ids.n1n_cygnus.opacity = 0.0
                        self.screens["usos"].ids.n1n_label.text = ""
                        self.screens["vv"].ids.n1n_label.text = ""
                        self.screens["vv"].ids.n1n_cygnus.opacity = 0.0
                    elif port == "Service Module Aft":
                        self.screens["rs"].ids.sma_mission.text = "-"
                        self.screens["rs"].ids.sma_vehicle.text = "-"
                        self.screens["rs"].ids.sma_spacecraft.text = "-"
                        self.screens["rs"].ids.sma_arrival.text = "-"
                        self.screens["rs"].ids.sma_departure.text = "-"
                        self.screens["rs"].ids.sma_label.text = ""
                        self.screens["vv"].ids.sma_label.text = ""
                        self.screens["rs"].ids.sma_soyuz.opacity = 0.0
                        self.screens["rs"].ids.sma_progress.opacity = 0.0
                        self.screens["vv"].ids.sma_soyuz.opacity = 0.0
                        self.screens["vv"].ids.sma_progress.opacity = 0.0
                    elif port == "MRM-2 Zenith":
                        self.screens["rs"].ids.mrm2_mission.text = "-"
                        self.screens["rs"].ids.mrm2_vehicle.text = "-"
                        self.screens["rs"].ids.mrm2_spacecraft.text = "-"
                        self.screens["rs"].ids.mrm2_arrival.text = "-"
                        self.screens["rs"].ids.mrm2_departure.text = "-"
                        self.screens["rs"].ids.mrm2_label.text = ""
                        self.screens["vv"].ids.mrm2_label.text = ""
                        self.screens["rs"].ids.mrm2_soyuz.opacity = 0.0
                        self.screens["rs"].ids.mrm2_progress.opacity = 0.0
                        self.screens["vv"].ids.mrm2_soyuz.opacity = 0.0
                        self.screens["vv"].ids.mrm2_progress.opacity = 0.0
                    elif port == "MRM-1 Nadir":
                        self.screens["rs"].ids.mrm1_mission.text = "-"
                        self.screens["rs"].ids.mrm1_vehicle.text = "-"
                        self.screens["rs"].ids.mrm1_spacecraft.text = "-"
                        self.screens["rs"].ids.mrm1_arrival.text = "-"
                        self.screens["rs"].ids.mrm1_departure.text = "-"
                        self.screens["rs"].ids.mrm1_label.text = ""
                        self.screens["vv"].ids.mrm1_label.text = ""
                        self.screens["rs"].ids.mrm1_soyuz.opacity = 0.0
                        self.screens["rs"].ids.mrm1_progress.opacity = 0.0
                        self.screens["vv"].ids.mrm1_soyuz.opacity = 0.0
                        self.screens["vv"].ids.mrm1_progress.opacity = 0.0
                    elif port == "RS Node Nadir":
                        self.screens["rs"].ids.rsn_mission.text = "-"
                        self.screens["rs"].ids.rsn_vehicle.text = "-"
                        self.screens["rs"].ids.rsn_spacecraft.text = "-"
                        self.screens["rs"].ids.rsn_arrival.text = "-"
                        self.screens["rs"].ids.rsn_departure.text = "-"
                        self.screens["rs"].ids.rsn_label.text = ""
                        self.screens["vv"].ids.rsn_label.text = ""
                        self.screens["rs"].ids.rsn_soyuz.opacity = 0.0
                        self.screens["rs"].ids.rsn_progress.opacity = 0.0
                        self.screens["vv"].ids.rsn_soyuz.opacity = 0.0
                        self.screens["vv"].ids.rsn_progress.opacity = 0.0

            else:
                log_error("Table 'vehicles' does not exist.")
        except sqlite3.Error as e:
            log_error(f"SQLite error: {e}")
        except Exception as e:
            log_error(f"General error: {e}")

    def ros_range_moving_average(self, new_value, size: int) -> float:
        """
        Keep the last *size* samples and return their average.
        The deque's maxlen enforces the window automatically.
        """
        if self.ros_data.maxlen != size:          # resize on the fly if needed
            self.ros_data = deque(self.ros_data, maxlen=size)

        self.ros_data.append(new_value)           # oldest item auto-drops here
        return sum(self.ros_data) / len(self.ros_data)

    def update_labels(self, dt): #THIS IS THE IMPORTANT FUNCTION
        global mimicbutton, switchtofake, demoboolean, runningDemo, playbackboolean, psarj2, ssarj2, aos, los, oldLOS, psarjmc, ssarjmc, ptrrjmc, strrjmc, beta1bmc, beta1amc, beta2bmc, beta2amc, beta3bmc, beta3amc, beta4bmc, beta4amc, US_EVAinProgress, position_x, position_y, position_z, velocity_x, velocity_y, velocity_z, altitude, velocity, iss_mass, testvalue, testfactor, airlock_pump, crewlockpres, leak_hold, firstcrossing, EVA_activities, repress, depress, oldAirlockPump, obtained_EVA_crew, EVAstartTime
        global holdstartTime, LS_Subscription
        global Disco, eva, standby, prebreath1, prebreath2, depress1, depress2, leakhold, repress
        global EPSstorageindex, channel1A_voltage, channel1B_voltage, channel2A_voltage, channel2B_voltage, channel3A_voltage, channel3B_voltage, channel4A_voltage, channel4B_voltage, USOS_Power
        global stationmode, sgant_elevation, sgant_xelevation
        global tdrs, module
        global old_mt_timestamp, old_mt_position, mt_speed

        if runningDemo:
            self.screens["playback"].ids.DemoStart.disabled = True
            self.screens["playback"].ids.HTVDemoStart.disabled = True
            self.screens["playback"].ids.DemoStop.disabled = False
            self.screens["playback"].ids.HTVDemoStop.disabled = False
            self.screens["playback"].ids.OFT2DemoStart.disabled = True
            self.screens["playback"].ids.OFT2DemoStop.disabled = False
            self.screens["playback"].ids.arduino.source = mimic_directory + "/Mimic/Pi/imgs/signal/Arduino_Transmit.zip"

        c.execute('select Value from telemetry')
        values = c.fetchall()
        c.execute('select Timestamp from telemetry')
        timestamps = c.fetchall()

        sub_status = str((values[255])[0]) #lightstreamer subscript checker
        client_status = str((values[256])[0]) #lightstreamer client checker

        psarj = "{:.2f}".format(float((values[0])[0]))
        if not switchtofake:
            psarj2 = float(psarj)
        if not App.get_running_app().manual_control:
            psarjmc = float(psarj)
        ssarj = "{:.2f}".format(float((values[1])[0]))
        if not switchtofake:
            ssarj2 = float(ssarj)
        if not App.get_running_app().manual_control:
            ssarjmc = float(ssarj)
        ptrrj = "{:.2f}".format(float((values[2])[0]))
        if not App.get_running_app().manual_control:
            ptrrjmc = float(ptrrj)
        strrj = "{:.2f}".format(float((values[3])[0]))
        if not App.get_running_app().manual_control:
            strrjmc = float(strrj)
        beta1b = "{:.2f}".format(float((values[4])[0]))
        if not switchtofake:
            beta1b2 = float(beta1b)
        if not App.get_running_app().manual_control:
            beta1bmc = float(beta1b)
        beta1a = "{:.2f}".format(float((values[5])[0]))
        if not switchtofake:
            beta1a2 = float(beta1a)
        if not App.get_running_app().manual_control:
            beta1amc = float(beta1a)
        beta2b = "{:.2f}".format(float((values[6])[0]))
        if not switchtofake:
            beta2b2 = float(beta2b) #+ 20.00
        if not App.get_running_app().manual_control:
            beta2bmc = float(beta2b)
        beta2a = "{:.2f}".format(float((values[7])[0]))
        if not switchtofake:
            beta2a2 = float(beta2a)
        if not App.get_running_app().manual_control:
            beta2amc = float(beta2a)
        beta3b = "{:.2f}".format(float((values[8])[0]))
        if not switchtofake:
            beta3b2 = float(beta3b)
        if not App.get_running_app().manual_control:
            beta3bmc = float(beta3b)
        beta3a = "{:.2f}".format(float((values[9])[0]))
        if not switchtofake:
            beta3a2 = float(beta3a)
        if not App.get_running_app().manual_control:
            beta3amc = float(beta3a)
        beta4b = "{:.2f}".format(float((values[10])[0]))
        if not switchtofake:
            beta4b2 = float(beta4b)
        if not App.get_running_app().manual_control:
            beta4bmc = float(beta4b)
        beta4a = "{:.2f}".format(float((values[11])[0]))
        if not switchtofake:
            beta4a2 = float(beta4a) #+ 20.00
        if not App.get_running_app().manual_control:
            beta4amc = float(beta4a)

        aos = "{:.2f}".format(int((values[12])[0]))
        los = "{:.2f}".format(int((values[13])[0]))
        sasa_el = "{:.2f}".format(float((values[14])[0]))
        sasa_az = "{:.2f}".format(float((values[18])[0]))
        active_sasa = int((values[54])[0])
        sasa1_active = int((values[53])[0])
        sasa2_active = int((values[52])[0])
        if sasa1_active or sasa2_active:
            sasa_xmit = True
        else:
            sasa_xmit = False
        sgant_elevation = float((values[15])[0])
        sgant_xelevation = float((values[17])[0])
        sgant_transmit = float((values[41])[0])
        uhf1_power = int((values[233])[0]) #0 = off, 1 = on, 3 = failed
        uhf2_power = int((values[234])[0]) #0 = off, 1 = on, 3 = failed
        uhf_framesync = int((values[235])[0]) #1 or 0

        #initialize array statuses to discharge
        v1as = 1
        v1bs = 1
        v2as = 1
        v2bs = 1
        v3as = 1
        v3bs = 1
        v4as = 1
        v4bs = 1

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

        #TCS telemetry
        SWmode_loopA = int((values[43])[0])
        SWmode_loopB = int((values[42])[0])
        NH3flow_loopA = "{:.2f}".format(float((values[22])[0]))
        NH3flow_loopB = "{:.2f}".format(float((values[19])[0]))
        NH3outletPress_loopA = "{:.2f}".format(float((values[23])[0]))
        NH3outletPress_loopB = "{:.2f}".format(float((values[20])[0]))
        NH3outletTemp_loopA = "{:.2f}".format(float((values[24])[0]))
        NH3outletTemp_loopB = "{:.2f}".format(float((values[21])[0]))

        #Russian Telemetry
        ros_mode = int((values[46])[0])

        ros_mode_texts = {
            1.0: "Crew Rescue",
            2.0: "Survival",
            3.0: "Reboost",
            4.0: "Proximity Operations",
            5.0: "EVA",
            6.0: "Microgravity",
            7.0: "Standard"
        }

        self.screens["rs_dock"].ids.ros_mode.text = ros_mode_texts.get(ros_mode, "n/a")
        
        
        rs_att_mode = int((values[126])[0])
        rs_motion_control = int((values[127])[0])
        rs_prep_free_drift = int((values[128])[0])
        rs_thruster_operation = int((values[129])[0])
        rs_current_dynamic = int((values[130])[0]) 
        rs_kurs1_op = int((values[107])[0]) # 1 or 0
        rs_kurs2_op = int((values[108])[0]) # 1 or 0
        rs_p1p2_failure = int((values[109])[0]) # 1 or 0
        rs_kursp_test = int((values[112])[0]) # 1 or 0
        rs_functional_mode = int((values[115])[0]) # 1 or 0
        rs_standby_mode = int((values[116])[0]) # 1 or 0
        rs_sm_capture_signal = int((values[113])[0]) # 1 or 0
        rs_target_acquisition = int((values[114])[0]) # 1 or 0
        rs_sm_fwd_dock = int((values[118])[0]) # 1 or 0
        rs_sm_aft_dock = int((values[119])[0]) # 1 or 0
        rs_sm_nadir_dock = int((values[120])[0]) # missing from screen?
        rs_fgb_nadir_dock = int((values[121])[0]) # 1 or 0
        rs_sm_udm_dock = int((values[122])[0]) # 1 or 0
        rs_mrm1_dock = int((values[123])[0]) # 1 or 0
        rs_mrm2_dock = int((values[124])[0]) # 1 or 0
        rs_sm_docking_flag = int((values[117])[0]) # 1 or 0
        rs_sm_hooks = int((values[125])[0]) # 1 or 0
        
        ros_docking_range = float((values[110])[0])
        if rs_target_acquisition: 
            self.screens["rs_dock"].ids.sm_range.text = f"{ros_docking_range:0.2f} m"
            self.screens["rs_dock"].ids.sm_rate.text = f"{float((values[111])[0]):0.2f} m/s"
        else:
            self.screens["rs_dock"].ids.sm_range.text = "n/a"
            self.screens["rs_dock"].ids.sm_rate.text = "n/a"


        rs_att_mode_texts = {
            0.0: "Inertial",
            1.0: "LVLH SM",
            2.0: "Solar Orientation",
            3.0: "Current LVLH",
            4.0: "Current Inertial Attitude",
            5.0: "Damping",
            6.0: "TEA",
            7.0: "X-POP"
        }
        
        rs_motion_control_texts = {
            0.0: "Undetermined State",
            1.0: "RS Master"
        }

        rs_prep_free_drift_texts = {
            0.0: "Undetermined State",
            1.0: "Prepared to Free Drift"
        }

        rs_thruster_operation_texts = {
            0.0: "Pre-Starting Procedure",
            1.0: "Thruster Operation Terminated"
        }

        rs_current_dynamic_texts = {
            0.0: "Reserve",
            1.0: "Thrusters",
            2.0: "Gyrodines",
            3.0: "Gyrodines Desat (US Method)",
            4.0: "Gyrodines Desat (RS Method)",
            5.0: "Translational Thrusters",
            6.0: "Thrusters help CMG",
            7.0: "Free Drift"
        }

        rs_docking_port_texts = {
            0.0: "Undetermined State",
            1.0: "Docking Port Engaged"
        }
        
        rs_vv_docking_port_texts = {
            0.0: "Undetermined State",
            1.0: "Soyuz/Progress Docked"
        }

        rs_signal_texts = {
            0.0: "Undetermined State",
            1.0: "Yes"
        }
        
        rs_hooks_texts = {
            0.0: "Undetermined State",
            1.0: "Hooks Closed"
        }
        
        rs_sm_docking_flag_texts = {
            0.0: "Undetermined State",
            1.0: "Docking Flag Active"
        }
        
        self.screens["rs_dock"].ids.active_attitude.text = rs_att_mode_texts.get(rs_att_mode, "n/a")
        self.screens["rs_dock"].ids.motion_control.text = rs_motion_control_texts.get(rs_motion_control, "n/a")
        self.screens["rs_dock"].ids.prep_free_drift.text = rs_prep_free_drift_texts.get(rs_prep_free_drift, "n/a")
        self.screens["rs_dock"].ids.thruster_operation.text = rs_thruster_operation_texts.get(rs_thruster_operation, "n/a")
        self.screens["rs_dock"].ids.current_dynamic.text = rs_current_dynamic_texts.get(rs_current_dynamic, "n/a")
        
        self.screens["rs_dock"].ids.kurs1_operating.text = rs_signal_texts.get(rs_kurs1_op, "n/a")
        self.screens["rs_dock"].ids.kurs2_operating.text = rs_signal_texts.get(rs_kurs2_op, "n/a")
        self.screens["rs_dock"].ids.p1p2_failure.text = rs_signal_texts.get(rs_p1p2_failure, "n/a")
        self.screens["rs_dock"].ids.kursp_test_mode.text = rs_signal_texts.get(rs_kursp_test, "n/a")
        self.screens["rs_dock"].ids.functional_mode.text = rs_signal_texts.get(rs_functional_mode, "n/a")
        self.screens["rs_dock"].ids.standby_mode.text = rs_signal_texts.get(rs_standby_mode, "n/a")
        self.screens["rs_dock"].ids.sm_capture_signal.text = rs_signal_texts.get(rs_sm_capture_signal, "n/a")
        self.screens["rs_dock"].ids.target_acquisition.text = rs_signal_texts.get(rs_target_acquisition, "n/a")
        
        self.screens["rs_dock"].ids.sm_fwd_dock.text = rs_docking_port_texts.get(rs_sm_fwd_dock, "n/a") + " (FGB)"
        self.screens["rs_dock"].ids.sm_aft_dock.text = rs_vv_docking_port_texts.get(rs_sm_aft_dock, "n/a")
        self.screens["rs_dock"].ids.sm_nadir_dock.text = rs_docking_port_texts.get(rs_sm_nadir_dock, "n/a") + " (MLM)"
        self.screens["rs_dock"].ids.fgb_nadir_dock.text = rs_docking_port_texts.get(rs_fgb_nadir_dock, "n/a") + " (MRM-1)"
        self.screens["rs_dock"].ids.sm_udm_dock.text = rs_vv_docking_port_texts.get(rs_sm_udm_dock, "n/a")
        self.screens["rs_dock"].ids.mrm1_dock.text = rs_vv_docking_port_texts.get(rs_mrm1_dock, "n/a")
        self.screens["rs_dock"].ids.mrm2_dock.text = rs_vv_docking_port_texts.get(rs_mrm2_dock, "n/a")
        
        self.screens["rs_dock"].ids.sm_docking_flag.text = rs_sm_docking_flag_texts.get(rs_sm_docking_flag, "n/a")
        self.screens["rs_dock"].ids.sm_hooks.text = rs_hooks_texts.get(rs_sm_hooks, "n/a")


        #ros_docking_range = float((values[110])[0])
        ros_docking_avg = self.ros_range_moving_average(ros_docking_range,10)

        if rs_target_acquisition and ros_docking_avg <= 80000:
            self.screens["rs_dock"].ids.dock_in_progress.text = "DOCKING IN PROGRESS"
            self.screens["rs_dock"].ids.dock_in_progress.color = (0,0,1,1)
            self.screens["rs_dock"].update_docking_bar_width(ros_docking_avg)
            if rs_sm_docking_flag:
                self.screens["rs_dock"].ids.dock_in_progress.text = "DOCKING COMPLETE!"
                self.screens["rs_dock"].ids.dock_in_progress.color = (0,1,0,1)
        else:
            self.screens["rs_dock"].ids.dock_in_progress.color = (0,0,0,0)
            self.screens["rs_dock"].update_docking_bar_width(ros_docking_avg)
         
        # Docking progress bar testing
        #value = 15000 
        #self.screens["rs_dock"].update_docking_bar_width(value)


        #MBS and MT telemetry
        mt_worksite = int((values[258])[0])
        self.screens["mt"].ids.mt_ws_value.text = str(mt_worksite)
        mt_position = float((values[257])[0])
        mt_position_timestamp = float((timestamps[257])[0])

        def map_mt_value(value):
            mt_min_value = 2000.0 #minimum mt position float value, rough guess needs refining
            mt_max_value = -2000.0 #maximum mt position float value, rough guess needs refining
            min_mt_mapped_value = 0.4 #change this to be leftmost kivy screen percentage of truss image
            max_mt_mapped_value = 0.9 #change this to be rightmost kivy screen percentage of truss image
        
            # Calculate the ratio of the input value within the range
            ratio = (value - mt_min_value) / (mt_max_value - mt_min_value)
        
            # Map the ratio to the desired output range
            mt_mapped_value = min_mt_mapped_value + ratio * (max_mt_mapped_value - min_mt_mapped_value)
        
            return mt_mapped_value #this should be the new pos_hint_x value
        
        self.screens["mt"].ids.FloatingMT.pos_hint = {"center_x": map_mt_value(mt_position),"center_y": 0.375}
            
        self.screens["mt"].ids.mt_position_value.text = str(mt_position)

        if (mt_position_timestamp - old_mt_timestamp) > 0:
            mt_speed = (mt_position - old_mt_position) / ((mt_position_timestamp - old_mt_timestamp)*3600)
            old_mt_timestamp = mt_position_timestamp
            old_mt_position = mt_position
            roboflashevent = Clock.schedule_once(self.flashROBObutton, 1)
        self.screens["mt"].ids.mt_speed_value.text = "{:2.2f}".format(float(mt_speed)) + " cm/s"

        MCASpayload = int((values[292])[0])
        POApayload = int((values[294])[0])
        
        ##SSRMS telemetry
        OperatingBase = str((values[261])[0])
        BaseLocation = str((values[260])[0])
        TipLEEstatus = str((values[269])[0])
        SACSopBase = str((values[261])[0])
        ShoulderRoll = "{:.2f}".format(float((values[262])[0]))
        ShoulderYaw = "{:.2f}".format(float((values[263])[0]))
        ShoulderPitch = "{:.2f}".format(float((values[264])[0]))
        ElbowPitch = "{:.2f}".format(float((values[265])[0]))
        WristRoll = "{:.2f}".format(float((values[268])[0]))
        WristYaw = "{:.2f}".format(float((values[267])[0]))
        WristPitch = "{:.2f}".format(float((values[266])[0]))
        
        ##SPDM Telemetry
        SPDMbase = str((values[271])[0])
        SPDMoperatingBase = str((values[270])[0])
        Shoulder1Roll = "{:.2f}".format(float((values[272])[0]))
        Shoulder1Yaw = "{:.2f}".format(float((values[273])[0]))
        Shoulder1Pitch = "{:.2f}".format(float((values[274])[0]))
        Elbow1Pitch = "{:.2f}".format(float((values[275])[0]))
        Wrist1Roll = "{:.2f}".format(float((values[278])[0]))
        Wrist1Yaw = "{:.2f}".format(float((values[277])[0]))
        Wrist1Pitch = "{:.2f}".format(float((values[276])[0]))
        Shoulder2Roll = "{:.2f}".format(float((values[280])[0]))
        Shoulder2Yaw = "{:.2f}".format(float((values[281])[0]))
        Shoulder2Pitch = "{:.2f}".format(float((values[282])[0]))
        Elbow2Pitch = "{:.2f}".format(float((values[283])[0]))
        Wrist2Roll = "{:.2f}".format(float((values[286])[0]))
        Wrist2Yaw = "{:.2f}".format(float((values[285])[0]))
        Wrist2Pitch = "{:.2f}".format(float((values[284])[0])) 
        Arm1OTCM = int((values[279])[0])
        Arm2OTCM = int((values[288])[0])
        BodyPayload = int((values[288])[0])
        BodyRoll = "{:.2f}".format(float((values[289])[0]))
                                       
        #ECLSS telemetry
        CabinTemp = "{:.2f}".format(float((values[195])[0]))
        CabinPress = "{:.2f}".format(float((values[194])[0]))
        CrewlockPress = "{:.2f}".format(float((values[16])[0]))
        AirlockPress = "{:.2f}".format(float((values[77])[0]))
        CleanWater = "{:.2f}".format(float((values[93])[0]))
        WasteWater = "{:.2f}".format(float((values[94])[0]))
        O2genState = str((values[95])[0])
        O2prodRate = "{:.2f}".format(float((values[96])[0]))
        VRSvlvPosition = str((values[198])[0])
        VESvlvPosition = str((values[199])[0])
        UrineProcessState = str((values[89])[0])
        UrineTank = "{:.2f}".format(float((values[90])[0]))
        WaterProcessState = str((values[91])[0])
        WaterProcessStep = str((values[92])[0])
        LTwater_Lab = "{:.2f}".format(float((values[192])[0]))
        MTwater_Lab = "{:.2f}".format(float((values[193])[0]))
        AC_LabPort = str((values[200])[0])
        AC_LabStbd = str((values[201])[0])
        FluidTempAir_Lab = "{:.2f}".format(float((values[197])[0]))
        FluidTempAv_Lab = "{:.2f}".format(float((values[196])[0]))
        LTwater_Node2 = "{:.2f}".format(float((values[82])[0]))
        MTwater_Node2 = "{:.2f}".format(float((values[81])[0]))
        AC_Node2 = str((values[83])[0])
        FluidTempAir_Node2 = "{:.2f}".format(float((values[84])[0]))
        FluidTempAv_Node2 = "{:.2f}".format(float((values[85])[0]))
        LTwater_Node3 = "{:.2f}".format(float((values[101])[0]))           
        MTwater_Node3 = "{:.2f}".format(float((values[99])[0]))            
        AC_Node3 = str((values[100])[0])
        FluidTempAir_Node3 = "{:.2f}".format(float((values[98])[0]))
        FluidTempAv_Node3 = "{:.2f}".format(float((values[97])[0]))
        
        #SASA telemetry
        ActiveString = str((values[54])[0])
        RFG1status = str((values[53])[0])
        RFG1azimuth = "{:.2f}".format(float((values[18])[0]))
        RFG1elev = "{:.2f}".format(float((values[14])[0]))
        RFG2status = str((values[52])[0])
        RFG2azimuth = "{:.2f}".format(float((values[51])[0]))
        RFG2elev = "{:.2f}".format(float((values[50])[0]))
        
        #UHF telemetry
        UHF1pwr = str((values[233])[0])
        UHF2pwr = str((values[234])[0])
        UHFframeSync = str((values[235])[0])
        
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

        def safe_divide(numerator, denominator):
            if denominator == 0:
                return 1
            else:
                return numerator / denominator

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

            v_radial = safe_divide(dot(vel_vec, pos_vec),pos_mag)

            h_mom = cross(pos_vec,vel_vec)
            h_mom_mag = math.sqrt(dot(h_mom,h_mom))

            inc = math.acos(safe_divide(h_mom[2],h_mom_mag))
            self.screens["orbit_data"].ids.inc.text = "{:.2f}".format(math.degrees(inc))
   
            node_vec = cross([0,0,1],h_mom)
            node_mag = math.sqrt(dot(node_vec,node_vec))

            raan = math.acos(safe_divide(node_vec[0],node_mag))
            if node_vec[1] < 0:
                raan = math.radians(360) - raan
            self.screens["orbit_data"].ids.raan.text = "{:.2f}".format(math.degrees(raan))

            pvnew = [x * (math.pow(vel_mag,2)-(mu/pos_mag)) for x in pos_vec]
            vvnew = [x * (pos_mag*v_radial) for x in vel_vec]
            e_vec1 = [(1/mu) * x for x in pvnew]
            e_vec2 = [(1/mu) * x for x in vvnew]
            e_vec = [e_vec1[0] - e_vec2[0],e_vec1[1] - e_vec2[1],e_vec1[2] - e_vec2[2] ]
            e_mag = math.sqrt(dot(e_vec,e_vec))
            self.screens["orbit_data"].ids.e.text = "{:.4f}".format(e_mag)

            arg_per = math.acos(safe_divide(dot(node_vec,e_vec),(node_mag*e_mag)))
            if e_vec[2] <= 0:
                arg_per = math.radians(360) - arg_per
            self.screens["orbit_data"].ids.arg_per.text = "{:.2f}".format(math.degrees(arg_per))

            ta = math.acos(safe_divide(dot(e_vec,pos_vec),(e_mag*pos_mag)))
            if v_radial <= 0:
                ta = math.radians(360) - ta
            self.screens["orbit_data"].ids.true_anomaly.text = "{:.2f}".format(math.degrees(ta))

            apogee = (math.pow(h_mom_mag,2)/mu)*(safe_divide(1,(1+e_mag*math.cos(math.radians(180)))))
            perigee = (math.pow(h_mom_mag,2)/mu)*(safe_divide(1,(1+e_mag*math.cos(0))))
            apogee_height = apogee - 6371.00
            perigee_height = perigee - 6371.00
            sma = 0.5*(apogee+perigee) #km
            if sma>=0:
                period = ((safe_divide(2*math.pi,math.sqrt(mu)))*math.pow(sma,3/2))/60 # minutes
            else:
                period = 0
            self.screens["orbit_data"].ids.apogee_height.text = str("{:.2f}".format(apogee_height))
            self.screens["orbit_data"].ids.perigee_height.text = str("{:.2f}".format(perigee_height))
       
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
        self.screens["eps"].ids.usos_power.text = str("{:.0f}".format(USOS_Power*-1.0)) + " W"
        self.screens["eps"].ids.solarbeta.text = str(solarbeta)

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
            self.screens["iss"].ids.stationmode_value.text = "Crew Rescue"
        elif stationmode == 2.0:
            self.screens["iss"].ids.stationmode_value.text = "Survival"
        elif stationmode == 3.0:
            self.screens["iss"].ids.stationmode_value.text = "Reboost"
        elif stationmode == 4.0:
            self.screens["iss"].ids.stationmode_value.text = "Proximity Operations"
        elif stationmode == 5.0:
            self.screens["iss"].ids.stationmode_value.text = "EVA"
        elif stationmode == 6.0:
            self.screens["iss"].ids.stationmode_value.text = "Microgravity"
        elif stationmode == 7.0:
            self.screens["iss"].ids.stationmode_value.text = "Standard"
        else:
            self.screens["iss"].ids.stationmode_value.text = "n/a"


        #Crew Screen Stuff
        
        #ISS has been crewed since 9:23 Nov 2nd 2000 UTC
        ISS_Expedition_1_Start = datetime(2000, 11, 2, 9, 23, 0)

        # Get the current date and time
        crew_now = datetime.now()

        # Calculate the difference including years, months, days, hours, minutes, and seconds
        crew_difference = relativedelta(crew_now, ISS_Expedition_1_Start)
        
        years_timedelta = crew_difference.years
        months_timedelta = crew_difference.months
        days_timedelta = crew_difference.days
        hours_timedelta = crew_difference.hours
        minutes_timedelta = crew_difference.minutes
        seconds_timedelta = crew_difference.seconds

        # Extract years, months, days, hours, minutes, and seconds
        self.screens["crew"].ids.ISS_crewed_years.text = str(years_timedelta)
        self.screens["crew"].ids.ISS_crewed_months.text = str(months_timedelta)
        self.screens["crew"].ids.ISS_crewed_days.text = str(days_timedelta)
        
        self.screens["crew"].ids.ISS_crewed_time.text = (f"{years_timedelta}:{months_timedelta:02}:{days_timedelta:02}/{hours_timedelta:02}:{minutes_timedelta:02}:{seconds_timedelta:02}")

        # Crew Launch Dates
        dragon10launch = datetime(2025, 3, 13) 
        soyuz73launch = datetime(2025, 4, 8) 

        # Calculate Days since crew launch
        dragon10count = (crew_now - dragon10launch).days
        soyuz73count = (crew_now - soyuz73launch).days

        # Calculate Cumulative Days for each astro
        dragon10_1 = 205+dragon10count
        dragon10_2 = 0+dragon10count
        dragon10_3 = 115+dragon10count
        dragon10_4 = 0+dragon10count
        soyuz73_1 = 357+soyuz73count
        soyuz73_2 = 0+soyuz73count
        soyuz73_3 = 0+soyuz73count

        #Identify variables for Crew Screen
        self.screens["crew"].ids.dragon10_1.text = str(dragon10count) + " / " + str(dragon10_1)
        self.screens["crew"].ids.dragon10_2.text = str(dragon10count) + " / " + str(dragon10_2)
        self.screens["crew"].ids.dragon10_3.text = str(dragon10count) + " / " + str(dragon10_3)
        self.screens["crew"].ids.dragon10_4.text = str(dragon10count) + " / " + str(dragon10_4)
        self.screens["crew"].ids.soyuz73_1.text = str(soyuz73count) + " / " + str(soyuz73_1)
        self.screens["crew"].ids.soyuz73_2.text = str(soyuz73count) + " / " + str(soyuz73_2)
        self.screens["crew"].ids.soyuz73_3.text = str(soyuz73count) + " / " + str(soyuz73_3)        

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

        self.screens["gnc"].ids.yaw.text = str("{:.2f}".format(yaw))
        self.screens["gnc"].ids.pitch.text = str("{:.2f}".format(pitch))
        self.screens["gnc"].ids.roll.text = str("{:.2f}".format(roll))

        self.screens["gnc"].ids.cmgsaturation.value = CMGmompercent
        self.screens["gnc"].ids.cmgsaturation_value.text = "CMG Saturation " + str("{:.1f}".format(CMGmompercent)) + "%"

        if cmg1_active == 1:
            self.screens["gnc"].ids.cmg1.source = mimic_directory + "/Mimic/Pi/imgs/gnc/cmg.png"
        else:
            self.screens["gnc"].ids.cmg1.source = mimic_directory + "/Mimic/Pi/imgs/gnc/cmg_offline.png"

        if cmg2_active == 1:
            self.screens["gnc"].ids.cmg2.source = mimic_directory + "/Mimic/Pi/imgs/gnc/cmg.png"
        else:
            self.screens["gnc"].ids.cmg2.source = mimic_directory + "/Mimic/Pi/imgs/gnc/cmg_offline.png"

        if cmg3_active == 1:
            self.screens["gnc"].ids.cmg3.source = mimic_directory + "/Mimic/Pi/imgs/gnc/cmg.png"
        else:
            self.screens["gnc"].ids.cmg3.source = mimic_directory + "/Mimic/Pi/imgs/gnc/cmg_offline.png"

        if cmg4_active == 1:
            self.screens["gnc"].ids.cmg4.source = mimic_directory + "/Mimic/Pi/imgs/gnc/cmg.png"
        else:
            self.screens["gnc"].ids.cmg4.source = mimic_directory + "/Mimic/Pi/imgs/gnc/cmg_offline.png"

        self.screens["gnc"].ids.cmg1spintemp.text = "Spin Temp " + str("{:.1f}".format(cmg1_spintemp))
        self.screens["gnc"].ids.cmg1halltemp.text = "Hall Temp " + str("{:.1f}".format(cmg1_halltemp))
        self.screens["gnc"].ids.cmg1vibration.text = "Vibration " + str("{:.4f}".format(cmg1_vibration))
        self.screens["gnc"].ids.cmg1current.text = "Current " + str("{:.1f}".format(cmg1_motorcurrent))
        self.screens["gnc"].ids.cmg1speed.text = "Speed " + str("{:.1f}".format(cmg1_wheelspeed))

        self.screens["gnc"].ids.cmg2spintemp.text = "Spin Temp " + str("{:.1f}".format(cmg2_spintemp))
        self.screens["gnc"].ids.cmg2halltemp.text = "Hall Temp " + str("{:.1f}".format(cmg2_halltemp))
        self.screens["gnc"].ids.cmg2vibration.text = "Vibration " + str("{:.4f}".format(cmg2_vibration))
        self.screens["gnc"].ids.cmg2current.text = "Current " + str("{:.1f}".format(cmg2_motorcurrent))
        self.screens["gnc"].ids.cmg2speed.text = "Speed " + str("{:.1f}".format(cmg2_wheelspeed))

        self.screens["gnc"].ids.cmg3spintemp.text = "Spin Temp " + str("{:.1f}".format(cmg3_spintemp))
        self.screens["gnc"].ids.cmg3halltemp.text = "Hall Temp " + str("{:.1f}".format(cmg3_halltemp))
        self.screens["gnc"].ids.cmg3vibration.text = "Vibration " + str("{:.4f}".format(cmg3_vibration))
        self.screens["gnc"].ids.cmg3current.text = "Current " + str("{:.1f}".format(cmg3_motorcurrent))
        self.screens["gnc"].ids.cmg3speed.text = "Speed " + str("{:.1f}".format(cmg3_wheelspeed))

        self.screens["gnc"].ids.cmg4spintemp.text = "Spin Temp " + str("{:.1f}".format(cmg4_spintemp))
        self.screens["gnc"].ids.cmg4halltemp.text = "Hall Temp " + str("{:.1f}".format(cmg4_halltemp))
        self.screens["gnc"].ids.cmg4vibration.text = "Vibration " + str("{:.4f}".format(cmg4_vibration))
        self.screens["gnc"].ids.cmg4current.text = "Current " + str("{:.1f}".format(cmg4_motorcurrent))
        self.screens["gnc"].ids.cmg4speed.text = "Speed " + str("{:.1f}".format(cmg4_wheelspeed))

        ##-------------------EPS Stuff---------------------------##

        #if halfavg_1a < 151.5: #discharging
        #    self.screens["eps"].ids.array_1a.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-discharging.zip"
        #    #self.screens["eps"].ids.array_1a.color = 1, 1, 1, 0.8
        #elif avg_1a > 160.0: #charged
        #    self.screens["eps"].ids.array_1a.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-charged.zip"
        #elif halfavg_1a >= 151.5:  #charging
        #    self.screens["eps"].ids.array_1a.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-charging.zip"
        #    self.screens["eps"].ids.array_1a.color = 1, 1, 1, 1.0
        #if float(c1a) > 0.0:    #power channel offline!
        #    self.screens["eps"].ids.array_1a.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-offline.png"

        #if halfavg_1b < 151.5: #discharging
        #    self.screens["eps"].ids.array_1b.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-discharging.zip"
        #    #self.screens["eps"].ids.array_1b.color = 1, 1, 1, 0.8
        #elif avg_1b > 160.0: #charged
        #    self.screens["eps"].ids.array_1b.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-charged.zip"
        #elif halfavg_1b >= 151.5:  #charging
        #    self.screens["eps"].ids.array_1b.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-charging.zip"
        #    self.screens["eps"].ids.array_1b.color = 1, 1, 1, 1.0
        #if float(c1b) > 0.0:                                  #power channel offline!
        #    self.screens["eps"].ids.array_1b.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-offline.png"

        #if halfavg_2a < 151.5: #discharging
        #    self.screens["eps"].ids.array_2a.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-discharging.zip"
        #    #self.screens["eps"].ids.array_2a.color = 1, 1, 1, 0.8
        #elif avg_2a > 160.0: #charged
        #    self.screens["eps"].ids.array_2a.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-charged.zip"
        #elif halfavg_2a >= 151.5:  #charging
        #    self.screens["eps"].ids.array_2a.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-charging.zip"
        #    self.screens["eps"].ids.array_2a.color = 1, 1, 1, 1.0
        #if float(c2a) > 0.0:                                  #power channel offline!
        #    self.screens["eps"].ids.array_2a.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-offline.png"

        #if halfavg_2b < 151.5: #discharging
        #    self.screens["eps"].ids.array_2b.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-discharging.zip"
        #    #self.screens["eps"].ids.array_2b.color = 1, 1, 1, 0.8
        #elif avg_2b > 160.0: #charged
        #    self.screens["eps"].ids.array_2b.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-charged.zip"
        #elif halfavg_2b >= 151.5:  #charging
        #    self.screens["eps"].ids.array_2b.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-charging.zip"
        #    self.screens["eps"].ids.array_2b.color = 1, 1, 1, 1.0
        #if float(c2b) > 0.0:                                  #power channel offline!
        #    self.screens["eps"].ids.array_2b.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-offline.png"

        #if halfavg_3a < 151.5: #discharging
        #    self.screens["eps"].ids.array_3a.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-discharging.zip"
            #self.screens["eps"].ids.array_3a.color = 1, 1, 1, 0.8
        #elif avg_3a > 160.0: #charged
        #    self.screens["eps"].ids.array_3a.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-charged.zip"
        #elif halfavg_3a >= 151.5:  #charging
        #    self.screens["eps"].ids.array_3a.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-charging.zip"
        #    self.screens["eps"].ids.array_3a.color = 1, 1, 1, 1.0
        #if float(c3a) > 0.0:                                  #power channel offline!
        #    self.screens["eps"].ids.array_3a.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-offline.png"

        #if halfavg_3b < 151.5: #discharging
        #    self.screens["eps"].ids.array_3b.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-discharging.zip"
            #self.screens["eps"].ids.array_3b.color = 1, 1, 1, 0.8
        #elif avg_3b > 160.0: #charged
        #    self.screens["eps"].ids.array_3b.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-charged.zip"
        #elif halfavg_3b >= 151.5:  #charging
        #    self.screens["eps"].ids.array_3b.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-charging.zip"
        #    self.screens["eps"].ids.array_3b.color = 1, 1, 1, 1.0
        #if float(c3b) > 0.0:                                  #power channel offline!
        #    self.screens["eps"].ids.array_3b.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-offline.png"

        #if halfavg_4a < 151.5: #discharging
        #    self.screens["eps"].ids.array_4a.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-discharging.zip"
        #    #self.screens["eps"].ids.array_4a.color = 1, 1, 1, 0.8
        #elif avg_4a > 160.0: #charged
        #    self.screens["eps"].ids.array_4a.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-charged.zip"
        #elif halfavg_4a >= 151.5:  #charging
        #    self.screens["eps"].ids.array_4a.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-charging.zip"
        #    self.screens["eps"].ids.array_4a.color = 1, 1, 1, 1.0
        #if float(c4a) > 0.0:                                  #power channel offline!
        #    self.screens["eps"].ids.array_4a.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-offline.png"

        #if halfavg_4b < 151.5: #discharging
        #    self.screens["eps"].ids.array_4b.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-discharging.zip"
        #    #self.screens["eps"].ids.array_4b.color = 1, 1, 1, 0.8
        #elif avg_4b > 160.0: #charged
        #    self.screens["eps"].ids.array_4b.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-charged.zip"
        #elif halfavg_4b >= 151.5:  #charging
        #    self.screens["eps"].ids.array_4b.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-charging.zip"
        #    self.screens["eps"].ids.array_4b.color = 1, 1, 1, 1.0
        #if float(c4b) > 0.0:                                  #power channel offline!
        #    self.screens["eps"].ids.array_4b.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-offline.png"
        #if avg_total_voltage > 151.5:
        #else:

        if float(v1a) >= 151.5 or float(v1b) >= 151.5 or float(v2a) >= 151.5 or float(v2b) >= 151.5 or float(v3a) >= 151.5 or float(v3b) >= 151.5 or float(v4a) >= 151.5 or float(v4b) >= 151.5:
            self.screens["eps"].ids.eps_sun.color = 1, 1, 1, 1
        else:
            self.screens["eps"].ids.eps_sun.color = 1, 1, 1, 0.1

        # array status numbers to be sent to arduino
        # 1 = discharging
        # 2 = charging
        # 3 = full
        # 4 = offline

        if float(v1a) < 151.5: #discharging
            self.screens["eps"].ids.array_1a.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-discharging.zip"
            v1as = 1
            #self.screens["eps"].ids.array_1a.color = 1, 1, 1, 0.8
        elif float(v1a) > 160.0: #charged
            self.screens["eps"].ids.array_1a.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-charged.zip"
            v1as = 3
        elif float(v1a) >= 151.5:  #charging
            self.screens["eps"].ids.array_1a.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-charging.zip"
            self.screens["eps"].ids.array_1a.color = 1, 1, 1, 1.0
            v1as = 2
        if float(c1a) > 0.0:    #power channel offline!
            self.screens["eps"].ids.array_1a.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-offline.png"
            v1as = 4

        if float(v1b) < 151.5: #discharging
            self.screens["eps"].ids.array_1b.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-discharging.zip"
            v1bs = 1
            #self.screens["eps"].ids.array_1b.color = 1, 1, 1, 0.8
        elif float(v1b) > 160.0: #charged
            self.screens["eps"].ids.array_1b.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-charged.zip"
            v1bs = 3
        elif float(v1b) >= 151.5:  #charging
            self.screens["eps"].ids.array_1b.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-charging.zip"
            self.screens["eps"].ids.array_1b.color = 1, 1, 1, 1.0
            v1bs = 2
        if float(c1b) > 0.0:                                  #power channel offline!
            self.screens["eps"].ids.array_1b.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-offline.png"
            v1bs = 4

        if float(v2a) < 151.5: #discharging
            self.screens["eps"].ids.array_2a.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-discharging.zip"
            v2as = 1
            #self.screens["eps"].ids.array_2a.color = 1, 1, 1, 0.8
        elif float(v2a) > 160.0: #charged
            self.screens["eps"].ids.array_2a.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-charged.zip"
            v2as = 3
        elif float(v2a) >= 151.5:  #charging
            self.screens["eps"].ids.array_2a.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-charging.zip"
            self.screens["eps"].ids.array_2a.color = 1, 1, 1, 1.0
            v2as = 2
        if float(c2a) > 0.0:                                  #power channel offline!
            self.screens["eps"].ids.array_2a.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-offline.png"
            v2as = 4

        if float(v2b) < 151.5: #discharging
            self.screens["eps"].ids.array_2b.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-discharging.zip"
            v2bs = 1
            #self.screens["eps"].ids.array_2b.color = 1, 1, 1, 0.8
        elif float(v2b) > 160.0: #charged
            self.screens["eps"].ids.array_2b.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-charged.zip"
            v2bs = 3
        elif float(v2b) >= 151.5:  #charging
            self.screens["eps"].ids.array_2b.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-charging.zip"
            self.screens["eps"].ids.array_2b.color = 1, 1, 1, 1.0
            v2bs = 2
        if float(c2b) > 0.0:                                  #power channel offline!
            self.screens["eps"].ids.array_2b.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-offline.png"
            v2bs = 4

        if float(v3a) < 151.5: #discharging
            self.screens["eps"].ids.array_3a.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-discharging.zip"
            v3as = 1
            #self.screens["eps"].ids.array_3a.color = 1, 1, 1, 0.8
        elif float(v3a) > 160.0: #charged
            self.screens["eps"].ids.array_3a.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-charged.zip"
            v3as = 3
        elif float(v3a) >= 151.5:  #charging
            self.screens["eps"].ids.array_3a.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-charging.zip"
            self.screens["eps"].ids.array_3a.color = 1, 1, 1, 1.0
            v3as = 2
        if float(c3a) > 0.0:                                  #power channel offline!
            self.screens["eps"].ids.array_3a.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-offline.png"
            v3as = 4

        if float(v3b) < 151.5: #discharging
            self.screens["eps"].ids.array_3b.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-discharging.zip"
            v3bs = 1
            #self.screens["eps"].ids.array_3b.color = 1, 1, 1, 0.8
        elif float(v3b) > 160.0: #charged
            self.screens["eps"].ids.array_3b.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-charged.zip"
            v3bs = 3
        elif float(v3b) >= 151.5:  #charging
            self.screens["eps"].ids.array_3b.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-charging.zip"
            self.screens["eps"].ids.array_3b.color = 1, 1, 1, 1.0
            v3bs = 2
        if float(c3b) > 0.0:                                  #power channel offline!
            self.screens["eps"].ids.array_3b.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-offline.png"
            v3bs = 4

        if float(v4a) < 151.5: #discharging
            self.screens["eps"].ids.array_4a.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-discharging.zip"
            v4as = 1
            #self.screens["eps"].ids.array_4a.color = 1, 1, 1, 0.8
        elif float(v4a) > 160.0: #charged
            self.screens["eps"].ids.array_4a.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-charged.zip"
            v4as = 3
        elif float(v4a) >= 151.5:  #charging
            self.screens["eps"].ids.array_4a.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-charging.zip"
            self.screens["eps"].ids.array_4a.color = 1, 1, 1, 1.0
            v4as = 2
        if float(c4a) > 0.0:                                  #power channel offline!
            self.screens["eps"].ids.array_4a.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-offline.png"
            v4as = 4
        
        if float(v4b) < 151.5: #discharging
            self.screens["eps"].ids.array_4b.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-discharging.zip"
            v4bs = 1
            #self.screens["eps"].ids.array_4b.color = 1, 1, 1, 0.8
        elif float(v4b) > 160.0: #charged
            self.screens["eps"].ids.array_4b.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-charged.zip"
            v4bs = 3
        elif float(v4b) >= 151.5:  #charging
            self.screens["eps"].ids.array_4b.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-charging.zip"
            self.screens["eps"].ids.array_4b.color = 1, 1, 1, 1.0
            v4bs = 2
        if float(c4b) > 0.0:                                  #power channel offline!
            self.screens["eps"].ids.array_4b.source = mimic_directory + "/Mimic/Pi/imgs/eps/array-offline.png"
            v4bs = 4

        ##-------------------C&T Functionality-------------------##
        self.screens["ct_sgant"].ids.sgant_dish.angle = float(sgant_elevation)
        self.screens["ct_sgant"].ids.sgant_elevation.text = "{:.2f}".format(float(sgant_elevation))

        #make sure radio animations turn off when no signal or no transmit
        if float(sgant_transmit) == 1.0 and float(aos) == 1.0:
            self.screens["ct_sgant"].ids.radio_up.color = 1, 1, 1, 1
            if "10" in tdrs:
                self.screens["ct_sgant"].ids.tdrs_west10.source = mimic_directory + "/Mimic/Pi/imgs/ct/TDRS.zip"
                self.screens["ct_sgant"].ids.tdrs_west11.source = mimic_directory + "/Mimic/Pi/imgs/ct/TDRS.png"
                self.screens["ct_sgant"].ids.tdrs_east12.source = mimic_directory + "/Mimic/Pi/imgs/ct/TDRS.png"
                self.screens["ct_sgant"].ids.tdrs_east6.source = mimic_directory + "/Mimic/Pi/imgs/ct/TDRS.png"
                self.screens["ct_sgant"].ids.tdrs_z7.source = mimic_directory + "/Mimic/Pi/imgs/ct/TDRS.png"
            if "11" in tdrs:
                self.screens["ct_sgant"].ids.tdrs_west11.source = mimic_directory + "/Mimic/Pi/imgs/ct/TDRS.zip"
                self.screens["ct_sgant"].ids.tdrs_west10.source = mimic_directory + "/Mimic/Pi/imgs/ct/TDRS.png"
                self.screens["ct_sgant"].ids.tdrs_east12.source = mimic_directory + "/Mimic/Pi/imgs/ct/TDRS.png"
                self.screens["ct_sgant"].ids.tdrs_east6.source = mimic_directory + "/Mimic/Pi/imgs/ct/TDRS.png"
                self.screens["ct_sgant"].ids.tdrs_z7.source = mimic_directory + "/Mimic/Pi/imgs/ct/TDRS.png"
            if "12" in tdrs:
                self.screens["ct_sgant"].ids.tdrs_west11.source = mimic_directory + "/Mimic/Pi/imgs/ct/TDRS.png"
                self.screens["ct_sgant"].ids.tdrs_west10.source = mimic_directory + "/Mimic/Pi/imgs/ct/TDRS.png"
                self.screens["ct_sgant"].ids.tdrs_east12.source = mimic_directory + "/Mimic/Pi/imgs/ct/TDRS.zip"
                self.screens["ct_sgant"].ids.tdrs_east6.source = mimic_directory + "/Mimic/Pi/imgs/ct/TDRS.png"
                self.screens["ct_sgant"].ids.tdrs_z7.source = mimic_directory + "/Mimic/Pi/imgs/ct/TDRS.png"
            if "6" in tdrs:
                self.screens["ct_sgant"].ids.tdrs_west11.source = mimic_directory + "/Mimic/Pi/imgs/ct/TDRS.png"
                self.screens["ct_sgant"].ids.tdrs_west10.source = mimic_directory + "/Mimic/Pi/imgs/ct/TDRS.png"
                self.screens["ct_sgant"].ids.tdrs_east6.source = mimic_directory + "/Mimic/Pi/imgs/ct/TDRS.zip"
                self.screens["ct_sgant"].ids.tdrs_east12.source = mimic_directory + "/Mimic/Pi/imgs/ct/TDRS.png"
                self.screens["ct_sgant"].ids.tdrs_z7.source = mimic_directory + "/Mimic/Pi/imgs/ct/TDRS.png"
            if "7" in tdrs:
                self.screens["ct_sgant"].ids.tdrs_west11.source = mimic_directory + "/Mimic/Pi/imgs/ct/TDRS.png"
                self.screens["ct_sgant"].ids.tdrs_west10.source = mimic_directory + "/Mimic/Pi/imgs/ct/TDRS.png"
                self.screens["ct_sgant"].ids.tdrs_east6.source = mimic_directory + "/Mimic/Pi/imgs/ct/TDRS.png"
                self.screens["ct_sgant"].ids.tdrs_east12.source = mimic_directory + "/Mimic/Pi/imgs/ct/TDRS.png"
                self.screens["ct_sgant"].ids.tdrs_z7.source = mimic_directory + "/Mimic/Pi/imgs/ct/TDRS.zip"

        elif float(aos) == 0.0 and (float(sgant_transmit) == 0.0 or float(sgant_transmit) == 1.0):
            self.screens["ct_sgant"].ids.radio_up.color = 0, 0, 0, 0
            self.screens["ct_sgant"].ids.tdrs_east12.source = mimic_directory + "/Mimic/Pi/imgs/ct/TDRS.png"
            self.screens["ct_sgant"].ids.tdrs_east6.source = mimic_directory + "/Mimic/Pi/imgs/ct/TDRS.png"
            self.screens["ct_sgant"].ids.tdrs_west11.source = mimic_directory + "/Mimic/Pi/imgs/ct/TDRS.png"
            self.screens["ct_sgant"].ids.tdrs_west10.source = mimic_directory + "/Mimic/Pi/imgs/ct/TDRS.png"
            self.screens["ct_sgant"].ids.tdrs_z7.source = mimic_directory + "/Mimic/Pi/imgs/ct/TDRS.png"

        #now check main CT screen radio signal
        if float(sgant_transmit) == 1.0 and float(aos) == 1.0:
            self.screens["ct"].ids.sgant1_radio.color = 1, 1, 1, 1
            self.screens["ct"].ids.sgant2_radio.color = 1, 1, 1, 1
        elif float(sgant_transmit) == 1.0 and float(aos) == 0.0:
            self.screens["ct"].ids.sgant1_radio.color = 0, 0, 0, 0
            self.screens["ct"].ids.sgant2_radio.color = 0, 0, 0, 0
        elif float(sgant_transmit) == 0.0:
            self.screens["ct"].ids.sgant1_radio.color = 0, 0, 0, 0
            self.screens["ct"].ids.sgant2_radio.color = 0, 0, 0, 0
        elif float(aos) == 0.0:
            self.screens["ct"].ids.sgant1_radio.color = 0, 0, 0, 0
            self.screens["ct"].ids.sgant2_radio.color = 0, 0, 0, 0

        if float(sasa1_active) == 1.0 and float(aos) == 1.0:
            self.screens["ct"].ids.sasa1_radio.color = 1, 1, 1, 1
        elif float(sasa1_active) == 1.0 and float(aos) == 0.0:
            self.screens["ct"].ids.sasa1_radio.color = 0, 0, 0, 0
        elif float(sasa1_active) == 0.0:
            self.screens["ct"].ids.sasa1_radio.color = 0, 0, 0, 0
        elif float(aos) == 0.0:
            self.screens["ct"].ids.sasa1_radio.color = 0, 0, 0, 0


        if float(sasa2_active) == 1.0 and float(aos) == 1.0:
            self.screens["ct"].ids.sasa2_radio.color = 1, 1, 1, 1
        elif float(sasa2_active) == 1.0 and float(aos) == 0.0:
            self.screens["ct"].ids.sasa2_radio.color = 0, 0, 0, 0
        elif float(sasa2_active) == 0.0:
            self.screens["ct"].ids.sasa2_radio.color = 0, 0, 0, 0
        elif float(aos) == 0.0:
            self.screens["ct"].ids.sasa2_radio.color = 0, 0, 0, 0

        if float(uhf1_power) == 1.0 and float(aos) == 1.0:
            self.screens["ct"].ids.uhf1_radio.color = 1, 1, 1, 1
        elif float(uhf1_power) == 1.0 and float(aos) == 0.0:
            self.screens["ct"].ids.uhf1_radio.color = 1, 0, 0, 1
        elif float(uhf1_power) == 0.0:
            self.screens["ct"].ids.uhf1_radio.color = 0, 0, 0, 0

        if float(uhf2_power) == 1.0 and float(aos) == 1.0:
            self.screens["ct"].ids.uhf2_radio.color = 1, 1, 1, 1
        elif float(uhf2_power) == 1.0 and float(aos) == 0.0:
            self.screens["ct"].ids.uhf2_radio.color = 1, 0, 0, 1
        elif float(uhf2_power) == 0.0:
            self.screens["ct"].ids.uhf2_radio.color = 0, 0, 0, 0

        ##-------------------US EVA Functionality-------------------##

        if airlock_pump_voltage == 1:
            self.screens["us_eva"].ids.pumpvoltage.text = "Airlock Pump Power On!"
            self.screens["us_eva"].ids.pumpvoltage.color = 0.33, 0.7, 0.18
        else:
            self.screens["us_eva"].ids.pumpvoltage.text = "Airlock Pump Power Off"
            self.screens["us_eva"].ids.pumpvoltage.color = 0, 0, 0

        if airlock_pump_switch == 1:
            self.screens["us_eva"].ids.pumpswitch.text = "Airlock Pump Active!"
            self.screens["us_eva"].ids.pumpswitch.color = 0.33, 0.7, 0.18
        else:
            self.screens["us_eva"].ids.pumpswitch.text = "Airlock Pump Inactive"
            self.screens["us_eva"].ids.pumpswitch.color = 0, 0, 0

        ##activate EVA button flash
        if (airlock_pump_voltage == 1 or crewlockpres < 734):
            usevaflashevent = Clock.schedule_once(self.flashUS_EVAbutton, 1)

        ##No EVA Currently
        if airlock_pump_voltage == 0 and airlock_pump_switch == 0 and crewlockpres > 737 and airlockpres > 740:
            eva = False
            self.screens["us_eva"].ids.leak_timer.text = ""
            self.screens["us_eva"].ids.Crewlock_Status_image.source = mimic_directory + '/Mimic/Pi/imgs/eva/BlankLights.png'
            self.screens["us_eva"].ids.EVA_occuring.color = 1, 0, 0
            self.screens["us_eva"].ids.EVA_occuring.text = "Currently No EVA"

        ##EVA Standby - NOT UNIQUE
        if airlock_pump_voltage == 1 and airlock_pump_switch == 1 and crewlockpres > 740 and airlockpres > 740:
            standby = True
            self.screens["us_eva"].ids.leak_timer.text = "~160s Leak Check"
            self.screens["us_eva"].ids.Crewlock_Status_image.source = mimic_directory + '/Mimic/Pi/imgs/eva/StandbyLights.png'
            self.screens["us_eva"].ids.EVA_occuring.color = 0, 0, 1
            self.screens["us_eva"].ids.EVA_occuring.text = "EVA Standby"
        else:
            standby = False

        ##EVA Prebreath Pressure
        if airlock_pump_voltage == 1 and crewlockpres > 740 and airlockpres > 740:
            prebreath1 = True
            self.screens["us_eva"].ids.Crewlock_Status_image.source = mimic_directory + '/Mimic/Pi/imgs/eva/PreBreatheLights.png'
            self.screens["us_eva"].ids.leak_timer.text = "~160s Leak Check"
            self.screens["us_eva"].ids.EVA_occuring.color = 0, 0, 1
            self.screens["us_eva"].ids.EVA_occuring.text = "Pre-EVA Nitrogen Purge"

        ##EVA Depress1
        if airlock_pump_voltage == 1 and airlock_pump_switch == 1 and crewlockpres < 740 and airlockpres > 740:
            depress1 = True
            self.screens["us_eva"].ids.leak_timer.text = "~160s Leak Check"
            self.screens["us_eva"].ids.EVA_occuring.text = "Crewlock Depressurizing"
            self.screens["us_eva"].ids.EVA_occuring.color = 0, 0, 1
            self.screens["us_eva"].ids.Crewlock_Status_image.source = mimic_directory + '/Mimic/Pi/imgs/eva/DepressLights.png'

        ##EVA Leakcheck
        if airlock_pump_voltage == 1 and crewlockpres < 260 and crewlockpres > 250 and (depress1 or leakhold):
            if depress1:
                holdstartTime = float(unixconvert[7])*24+unixconvert[3]+float(unixconvert[4])/60+float(unixconvert[5])/3600
            leakhold = True
            depress1 = False
            self.screens["us_eva"].ids.EVA_occuring.text = "Leak Check in Progress!"
            self.screens["us_eva"].ids.EVA_occuring.color = 0, 0, 1
            Clock.schedule_once(self.hold_timer, 1)
            self.screens["us_eva"].ids.Crewlock_Status_image.source = mimic_directory + '/Mimic/Pi/imgs/eva/LeakCheckLights.png'
        else:
            leakhold = False

        ##EVA Depress2
        if airlock_pump_voltage == 1 and crewlockpres <= 250 and crewlockpres > 3:
            leakhold = False
            self.screens["us_eva"].ids.leak_timer.text = "Complete"
            self.screens["us_eva"].ids.EVA_occuring.text = "Crewlock Depressurizing"
            self.screens["us_eva"].ids.EVA_occuring.color = 0, 0, 1
            self.screens["us_eva"].ids.Crewlock_Status_image.source = mimic_directory + '/Mimic/Pi/imgs/eva/DepressLights.png'

        ##EVA in progress
        if crewlockpres < 2.5:
            eva = True
            self.screens["us_eva"].ids.EVA_occuring.text = "EVA In Progress!!!"
            self.screens["us_eva"].ids.EVA_occuring.color = 0.33, 0.7, 0.18
            self.screens["us_eva"].ids.leak_timer.text = "Complete"
            self.screens["us_eva"].ids.Crewlock_Status_image.source = mimic_directory + '/Mimic/Pi/imgs/eva/InProgressLights.png'
            evatimerevent = Clock.schedule_once(self.EVA_clock, 1)

        ##Repress - this one still did not work with the code changes I did for eva88 (June 2023)
        if airlock_pump_voltage == 1 and airlock_pump_switch == 1 and crewlockpres >= 3 and airlockpres < 734:
            eva = False
            self.screens["us_eva"].ids.EVA_occuring.color = 0, 0, 1
            self.screens["us_eva"].ids.EVA_occuring.text = "Crewlock Repressurizing"
            self.screens["us_eva"].ids.Crewlock_Status_image.source = mimic_directory + '/Mimic/Pi/imgs/eva/RepressLights.png'

        ##-------------------EVA Functionality End-------------------##

        #----------------------EVA EMU Telemetry-------------------#
        UIApowerEMU1 = "{:.2f}".format(float((values[61])[0]))
        UIApowerEMU2 = "{:.2f}".format(float((values[63])[0]))
        UIAcurrentEMU1 = "{:.2f}".format(float((values[62])[0]))
        UIAcurrentEMU2 = "{:.2f}".format(float((values[64])[0]))
        PSApowerEMU1 = "{:.2f}".format(float((values[67])[0]))
        PSApowerEMU2 = "{:.2f}".format(float((values[69])[0]))
        PSAcurrentEMU1 = "{:.2f}".format(float((values[68])[0]))
        PSAcurrentEMU2 = "{:.2f}".format(float((values[70])[0]))
        IRUvoltage = "{:.2f}".format(float((values[65])[0]))
        IRUcurrent = "{:.2f}".format(float((values[66])[0]))
        #--------------------EVA EMU Telemetry End------------------#

#        if (difference > -10) and (isinstance(App.get_running_app().root_window.children[0], Popup)==False):
#            LOSpopup = Popup(title='Loss of Signal', content=Label(text='Possible LOS Soon'), size_hint=(0.3, 0.2), auto_dismiss=True)
#            LOSpopup.open()

        ##-------------------Fake Orbit Simulator-------------------##
        #self.screens["playback"].ids.psarj.text = str(psarj)
        #self.screens["playback"].ids.ssarj.text = str(ssarj)
        #self.screens["playback"].ids.beta1a.text = str(beta1a)
        #self.screens["playback"].ids.beta1b.text = str(beta1b)
        #self.screens["playback"].ids.beta2a.text = str(beta2a)
        #self.screens["playback"].ids.beta2b.text = str(beta2b)
        #self.screens["playback"].ids.beta3a.text = str(beta3a)
        #self.screens["playback"].ids.beta3b.text = str(beta3b)
        #self.screens["playback"].ids.beta4a.text = str(beta4a)
        #self.screens["playback"].ids.beta4b.text = str(beta4b)

        if demoboolean:
            if Disco:
                serialWrite("Disco ")
                Disco = False
            #serialWrite("PSARJ=" + psarj + " " + "SSARJ=" + ssarj + " " + "PTRRJ=" + ptrrj + " " + "STRRJ=" + strrj + " " + "B1B=" + beta1b + " " + "B1A=" + beta1a + " " + "B2B=" + beta2b + " " + "B2A=" + beta2a + " " + "B3B=" + beta3b + " " + "B3A=" + beta3a + " " + "B4B=" + beta4b + " " + "B4A=" + beta4a + " " + "V1A=" + v1a + " " + "V2A=" + v2a + " " + "V3A=" + v3a + " " + "V4A=" + v4a + " " + "V1B=" + v1b + " " + "V2B=" + v2b + " " + "V3B=" + v3b + " " + "V4B=" + v4b + " ")
            serialWrite("PSARJ=" + psarj + " " + "SSARJ=" + ssarj + " " + "PTRRJ=" + ptrrj + " " + "STRRJ=" + strrj + " " + "B1B=" + beta1b + " " + "B1A=" + beta1a + " " + "B2B=" + beta2b + " " + "B2A=" + beta2a + " " + "B3B=" + beta3b + " " + "B3A=" + beta3a + " " + "B4B=" + beta4b + " " + "B4A=" + beta4a + " " + "AOS=" + aos + " " + "V1A=" + str(v1as) + " " + "V2A=" + str(v2as) + " " + "V3A=" + str(v3as) + " " + "V4A=" + str(v4as) + " " + "V1B=" + str(v1bs) + " " + "V2B=" + str(v2bs) + " " + "V3B=" + str(v3bs) + " " + "V4B=" + str(v4bs) + " " + "ISS=" + module + " " + "Sgnt_el=" + str(int(sgant_elevation)) + " " + "Sgnt_xel=" + str(int(sgant_xelevation)) + " " + "Sgnt_xmit=" + str(int(sgant_transmit)) + " " + "SASA_Xmit=" + str(int(sasa_xmit)) + " SASA_AZ=" + str(float(sasa_az)) + " SASA_EL=" + str(float(sasa_el)) + " ")

        self.screens["orbit_data"].ids.position_x.text = str("{:.2f}".format(position_x))
        self.screens["orbit_data"].ids.position_y.text = str("{:.2f}".format(position_y))
        self.screens["orbit_data"].ids.position_z.text = str("{:.2f}".format(position_z))
        self.screens["orbit_data"].ids.velocity_x.text = str("{:.2f}".format(velocity_x))
        self.screens["orbit_data"].ids.velocity_y.text = str("{:.2f}".format(velocity_y))
        self.screens["orbit_data"].ids.velocity_z.text = str("{:.2f}".format(velocity_z))
 
        self.screens["eps"].ids.psarj_value.text = psarj + "deg"
        self.screens["eps"].ids.ssarj_value.text = ssarj + "deg"
        self.screens["tcs"].ids.ptrrj_value.text = ptrrj + "deg"
        self.screens["tcs"].ids.strrj_value.text = strrj + "deg"

        SW_MODE_MAP = {
            1: "STANDBY",
            2: "RESTART",
            3: "CHECKOUT",
            4: "DIRECTED POS",
            5: "AUTOTRACK",
            6: "BLIND",
            7: "SHUTDOWN",
            8: "SWITCHOVER"
        }
        
        self.screens["tcs"].ids.SWmode_loopA.text = SW_MODE_MAP.get(SWmode_loopA, "UNKNOWN")
        self.screens["tcs"].ids.SWmode_loopB.text = SW_MODE_MAP.get(SWmode_loopB, "UNKNOWN")

            
        #self.screens["tcs"].ids.SWmode_loopA.text = str(SWmode_loopA)
        #self.screens["tcs"].ids.SWmode_loopB.text = str(SWmode_loopB)
        self.screens["tcs"].ids.NH3flow_loopA.text = str(NH3flow_loopA)
        self.screens["tcs"].ids.NH3flow_loopB.text = str(NH3flow_loopB)
        self.screens["tcs"].ids.NH3outletPress_loopA.text = str(NH3outletPress_loopA)
        self.screens["tcs"].ids.NH3outletPress_loopB.text = str(NH3outletPress_loopB)
        self.screens["tcs"].ids.NH3outletTemp_loopA.text = str(NH3outletTemp_loopA)
        self.screens["tcs"].ids.NH3outletTemp_loopB.text = str(NH3outletTemp_loopB)
        
        self.screens["eclss"].ids.CabinTemp.text = str(CabinTemp)
        self.screens["eclss"].ids.CabinPress.text = str(CabinPress)
        self.screens["eclss"].ids.CrewlockPress.text = str(CrewlockPress)
        self.screens["eclss"].ids.AirlockPress.text = str(AirlockPress)
        self.screens["eclss"].ids.CleanWater.text = str(CleanWater)
        self.screens["eclss"].ids.WasteWater.text = str(WasteWater)
        self.screens["eclss"].ids.O2prodRate.text = str(O2prodRate)
        
        #self.screens["eclss"].ids.O2genState.text = str(O2genState)
        if int(O2genState) == 1:
            self.screens["eclss"].ids.O2genState.text = "PROCESS"
        elif int(O2genState) == 2:
            self.screens["eclss"].ids.O2genState.text = "STANDBY"
        elif int(O2genState) == 3:
            self.screens["eclss"].ids.O2genState.text = "SHUTDOWN"
        elif int(O2genState) == 4:
            self.screens["eclss"].ids.O2genState.text = "STOP"
        elif int(O2genState) == 5:
            self.screens["eclss"].ids.O2genState.text = "VENT DOME"
        elif int(O2genState) == 6:
            self.screens["eclss"].ids.O2genState.text = "INERT DOME"
        elif int(O2genState) == 7:
            self.screens["eclss"].ids.O2genState.text = "FAST SHTDWN"
        elif int(O2genState) == 8:
            self.screens["eclss"].ids.O2genState.text = "N2 PURGE SHTDWN"
        else:
            self.screens["eclss"].ids.O2genState.text = "n/a"
        
        #self.screens["eclss"].ids.VRSvlvPosition.text = str(VRSvlvPosition)
        if int(VRSvlvPosition) == 0:
            self.screens["eclss"].ids.VRSvlvPosition.text = "FAIL"
        elif int(VRSvlvPosition) == 1:
            self.screens["eclss"].ids.VRSvlvPosition.text = "OPEN"
        elif int(VRSvlvPosition) == 2:
            self.screens["eclss"].ids.VRSvlvPosition.text = "CLSD"
        elif int(VRSvlvPosition) == 3:
            self.screens["eclss"].ids.VRSvlvPosition.text = "TRNS"
        else:
            self.screens["eclss"].ids.VESvlvPosition.text = "n/a"
        
        #self.screens["eclss"].ids.VESvlvPosition.text = str(VESvlvPosition)
        if int(VESvlvPosition) == 0:
            self.screens["eclss"].ids.VESvlvPosition.text = "FAIL"
        elif int(VESvlvPosition) == 1:
            self.screens["eclss"].ids.VESvlvPosition.text = "OPEN"
        elif int(VESvlvPosition) == 2:
            self.screens["eclss"].ids.VESvlvPosition.text = "CLSD"
        elif int(VESvlvPosition) == 3:
            self.screens["eclss"].ids.VESvlvPosition.text = "TRNS"
        else:
            self.screens["eclss"].ids.VESvlvPosition.text = "n/a"
        
        self.screens["wrm"].ids.UrineTank.text = str(UrineTank)
        self.screens["wrm"].ids.CleanWater.text = str(CleanWater)
        self.screens["wrm"].ids.WasteWater.text = str(WasteWater)
        
        #self.screens["wrm"].ids.UrineProcessState.text = str(UrineProcessState)
        if int(UrineProcessState) == 2:
            self.screens["wrm"].ids.UrineProcessState.text = "STOP"
        elif int(UrineProcessState) == 4:
            self.screens["wrm"].ids.UrineProcessState.text = "SHTDWN"
        elif int(UrineProcessState) == 8:
            self.screens["wrm"].ids.UrineProcessState.text = "MAINT"
        elif int(UrineProcessState) == 16:
            self.screens["wrm"].ids.UrineProcessState.text = "NORM"
        elif int(UrineProcessState) == 32:
            self.screens["wrm"].ids.UrineProcessState.text = "STBY"
        elif int(UrineProcessState) == 64:
            self.screens["wrm"].ids.UrineProcessState.text = "IDLE"
        elif int(UrineProcessState) == 128:
            self.screens["wrm"].ids.UrineProcessState.text = "INIT"
        else:
            self.screens["wrm"].ids.UrineProcessState.text = "n/a"
        
        #self.screens["wrm"].ids.WaterProcessState.text = str(WaterProcessState)
        if int(WaterProcessState) == 1:
            self.screens["wrm"].ids.WaterProcessState.text = "STOP"
        elif int(WaterProcessState) == 2:
            self.screens["wrm"].ids.WaterProcessState.text = "SHTDWN"
        elif int(WaterProcessState) == 3:
            self.screens["wrm"].ids.WaterProcessState.text = "STBY"
        elif int(WaterProcessState) == 4:
            self.screens["wrm"].ids.WaterProcessState.text = "PROC"
        elif int(WaterProcessState) == 5:
            self.screens["wrm"].ids.WaterProcessState.text = "HOT SVC"
        elif int(WaterProcessState) == 6:
            self.screens["wrm"].ids.WaterProcessState.text = "FLUSH"
        elif int(WaterProcessState) == 7:
            self.screens["wrm"].ids.WaterProcessState.text = "WARM SHTDWN"
        else:
            self.screens["wrm"].ids.WaterProcessState.text = "n/a"
        
        #self.screens["wrm"].ids.WaterProcessStep.text = str(WaterProcessStep)
        if int(WaterProcessStep) == 0:
            self.screens["wrm"].ids.WaterProcessStep.text = "NONE"
        elif int(WaterProcessStep) == 1:
            self.screens["wrm"].ids.WaterProcessStep.text = "VENT"
        elif int(WaterProcessStep) == 2:
            self.screens["wrm"].ids.WaterProcessStep.text = "HEATUP"
        elif int(WaterProcessStep) == 3:
            self.screens["wrm"].ids.WaterProcessStep.text = "OURGE"
        elif int(WaterProcessStep) == 4:
            self.screens["wrm"].ids.WaterProcessStep.text = "FLOW"
        elif int(WaterProcessStep) == 5:
            self.screens["wrm"].ids.WaterProcessStep.text = "TEST"
        elif int(WaterProcessStep) == 6:
            self.screens["wrm"].ids.WaterProcessStep.text = "TEST SV 1"
        elif int(WaterProcessStep) == 7:
            self.screens["wrm"].ids.WaterProcessStep.text = "TEST SV 2"
        elif int(WaterProcessStep) == 8:
            self.screens["wrm"].ids.WaterProcessStep.text = "SERVICE"
        else:
            self.screens["wrm"].ids.WaterProcessStep.text = "n/a"
        
        self.screens["iatcs"].ids.LTwater_Lab.text = str(LTwater_Lab)
        self.screens["iatcs"].ids.MTwater_Lab.text = str(MTwater_Lab)
        self.screens["iatcs"].ids.FluidTempAir_Lab.text = str(FluidTempAir_Lab)
        self.screens["iatcs"].ids.FluidTempAv_Lab.text = str(FluidTempAv_Lab)
        self.screens["iatcs"].ids.LTwater_Node2.text = str(LTwater_Node2)
        self.screens["iatcs"].ids.MTwater_Node2.text = str(MTwater_Node2)
        self.screens["iatcs"].ids.FluidTempAir_Node2.text = str(FluidTempAir_Node2)
        self.screens["iatcs"].ids.FluidTempAv_Node2.text = str(FluidTempAv_Node2)
        self.screens["iatcs"].ids.LTwater_Node3.text = str(LTwater_Node3)
        self.screens["iatcs"].ids.MTwater_Node3.text = str(MTwater_Node3)
        self.screens["iatcs"].ids.FluidTempAir_Node3.text = str(FluidTempAir_Node3)
        self.screens["iatcs"].ids.FluidTempAv_Node3.text = str(FluidTempAv_Node3)
        
        #self.screens["iatcs"].ids.AC_LabPort.text = str(WaterProcessStep)
        if int(AC_LabPort) == 0:
            self.screens["iatcs"].ids.AC_LabPort.text = "RESET"
        elif int(AC_LabPort) == 1:
            self.screens["iatcs"].ids.AC_LabPort.text = "DRAIN"
        elif int(AC_LabPort) == 2:
            self.screens["iatcs"].ids.AC_LabPort.text = "DRYOUT"
        elif int(AC_LabPort) == 3:
            self.screens["iatcs"].ids.AC_LabPort.text = "EIB OFF"
        elif int(AC_LabPort) == 4:
            self.screens["iatcs"].ids.AC_LabPort.text = "OFF"
        elif int(AC_LabPort) == 5:
            self.screens["iatcs"].ids.AC_LabPort.text = "ON"
        elif int(AC_LabPort) == 6:
            self.screens["iatcs"].ids.AC_LabPort.text = "STARTUP"
        elif int(AC_LabPort) == 7:
            self.screens["iatcs"].ids.AC_LabPort.text = "TEST2"
        else:
            self.screens["iatcs"].ids.AC_LabPort.text = "n/a"
        
        #self.screens["iatcs"].ids.AC_LabStbd.text = str(WaterProcessStep)
        if int(AC_LabStbd) == 0:
            self.screens["iatcs"].ids.AC_LabStbd.text = "RESET"
        elif int(AC_LabStbd) == 1:
            self.screens["iatcs"].ids.AC_LabStbd.text = "DRAIN"
        elif int(AC_LabStbd) == 2:
            self.screens["iatcs"].ids.AC_LabStbd.text = "DRYOUT"
        elif int(AC_LabStbd) == 3:
            self.screens["iatcs"].ids.AC_LabStbd.text = "EIB OFF"
        elif int(AC_LabStbd) == 4:
            self.screens["iatcs"].ids.AC_LabStbd.text = "OFF"
        elif int(AC_LabStbd) == 5:
            self.screens["iatcs"].ids.AC_LabStbd.text = "ON"
        elif int(AC_LabStbd) == 6:
            self.screens["iatcs"].ids.AC_LabStbd.text = "STARTUP"
        elif int(AC_LabStbd) == 7:
            self.screens["iatcs"].ids.AC_LabStbd.text = "TEST2"
        else:
            self.screens["iatcs"].ids.AC_LabStbd.text = "n/a"
        
        #self.screens["iatcs"].ids.AC_Node2.text = str(WaterProcessStep)
        if int(AC_Node2) == 0:
            self.screens["iatcs"].ids.AC_Node2.text = "RESET"
        elif int(AC_Node2) == 1:
            self.screens["iatcs"].ids.AC_Node2.text = "DRAIN"
        elif int(AC_Node2) == 2:
            self.screens["iatcs"].ids.AC_Node2.text = "DRYOUT"
        elif int(AC_Node2) == 3:
            self.screens["iatcs"].ids.AC_Node2.text = "EIB OFF"
        elif int(AC_Node2) == 4:
            self.screens["iatcs"].ids.AC_Node2.text = "OFF"
        elif int(AC_Node2) == 5:
            self.screens["iatcs"].ids.AC_Node2.text = "ON"
        elif int(AC_Node2) == 6:
            self.screens["iatcs"].ids.AC_Node2.text = "STARTUP"
        elif int(AC_Node2) == 7:
            self.screens["iatcs"].ids.AC_Node2.text = "TEST2"
        else:
            self.screens["iatcs"].ids.AC_Node2.text = "n/a"
        
        #self.screens["iatcs"].ids.AC_Node3.text = str(WaterProcessStep)
        if int(AC_Node3) == 0:
            self.screens["iatcs"].ids.AC_Node3.text = "RESET"
        elif int(AC_Node3) == 1:
            self.screens["iatcs"].ids.AC_Node3.text = "DRAIN"
        elif int(AC_Node3) == 2:
            self.screens["iatcs"].ids.AC_Node3.text = "DRYOUT"
        elif int(AC_Node3) == 3:
            self.screens["iatcs"].ids.AC_Node3.text = "EIB OFF"
        elif int(AC_Node3) == 4:
            self.screens["iatcs"].ids.AC_Node3.text = "OFF"
        elif int(AC_Node3) == 5:
            self.screens["iatcs"].ids.AC_Node3.text = "ON"
        elif int(AC_Node3) == 6:
            self.screens["iatcs"].ids.AC_Node3.text = "STARTUP"
        elif int(AC_Node3) == 7:
            self.screens["iatcs"].ids.AC_Node3.text = "TEST2"
        else:
            self.screens["iatcs"].ids.AC_Node3.text = "n/a"
        
        ##Summary Telemetery on Robo Screen
        self.screens["robo"].ids.mt_worksite.text = str(mt_worksite)
        
        #self.screens["robo"].ids.OperatingBase.text = str(OperatingBase)
        if int(OperatingBase) == 0:
            self.screens["robo"].ids.OperatingBase.text = "A"
        elif int(OperatingBase) == 5:
            self.screens["robo"].ids.OperatingBase.text = "B"
        else:
            self.screens["robo"].ids.OperatingBase.text = "n/a"
        
        #self.screens["robo"].ids.BaseLocation.text = str(BaseLocation)
        if int(BaseLocation) == 1:
            self.screens["robo"].ids.BaseLocation.text = "Lab"
        elif int(BaseLocation) == 2:
            self.screens["robo"].ids.BaseLocation.text = "Node 3"
        elif int(BaseLocation) == 4:
            self.screens["robo"].ids.BaseLocation.text = "Node 2"
        elif int(BaseLocation) == 7:
            self.screens["robo"].ids.BaseLocation.text = "MBS PDGF 1"
        elif int(BaseLocation) == 8:
            self.screens["robo"].ids.BaseLocation.text = "MBS PDGF 2"
        elif int(BaseLocation) == 11:
            self.screens["robo"].ids.BaseLocation.text = "MBS PDGF 3"
        elif int(BaseLocation) == 13:
            self.screens["robo"].ids.BaseLocation.text = "MBS PDGF 4"
        elif int(BaseLocation) == 14:
            self.screens["robo"].ids.BaseLocation.text = "FGB"
        elif int(BaseLocation) == 16:
            self.screens["robo"].ids.BaseLocation.text = "POA"
        elif int(BaseLocation) == 19:
            self.screens["robo"].ids.BaseLocation.text = "SSRMS Tip LEE"
        elif int(BaseLocation) == 63:
            self.screens["robo"].ids.BaseLocation.text = "Undefined"
        else:
            self.screens["robo"].ids.BaseLocation.text = "n/a"
        
        #self.screens["robo"].ids.SPDMbase.text = str(SPDMbase)
        if int(SPDMbase) == 1:
            self.screens["robo"].ids.SPDMbase.text = "US Lab"
        elif int(SPDMbase) == 2:
            self.screens["robo"].ids.SPDMbase.text = "Node 3"
        elif int(SPDMbase) == 4:
            self.screens["robo"].ids.SPDMbase.text = "Node 2"
        elif int(SPDMbase) == 7:
            self.screens["robo"].ids.SPDMbase.text = "MBS PDGF 1"
        elif int(SPDMbase) == 8:
            self.screens["robo"].ids.SPDMbase.text = "MBS PDGF 2"
        elif int(SPDMbase) == 11:
            self.screens["robo"].ids.SPDMbase.text = "MBS PDGF 3"
        elif int(SPDMbase) == 13:
            self.screens["robo"].ids.SPDMbase.text = "MBS PDGF 4"
        elif int(SPDMbase) ==14:
            self.screens["robo"].ids.SPDMbase.text = "FGB"
        elif int(SPDMbase) == 16:
            self.screens["robo"].ids.SPDMbase.text = "POA"
        elif int(SPDMbase) == 19:
            self.screens["robo"].ids.SPDMbase.text = "SSRMS Tip LEE"
        elif int(SPDMbase) == 63:
            self.screens["robo"].ids.SPDMbase.text = "Undefined"
        else:
            self.screens["robo"].ids.SPDMbase.text = "n/a"
        
        #self.screens["robo"].ids.SPDMoperatingBase.text = str(SPDMoperatingBase)
        if int(SPDMoperatingBase) == 1:
            self.screens["robo"].ids.SPDMoperatingBase.text = "SPDM Body LEE"
        elif int(SPDMoperatingBase) == 2:
            self.screens["robo"].ids.SPDMoperatingBase.text = "SPDM Body PDGF"
        else:
            self.screens["robo"].ids.SPDMoperatingBase.text = "n/a"

        #self.screens["mt"].ids.MCASpayload.text = str(MCASpayload)
        if int(MCASpayload) == 0:
            self.screens["mt"].ids.MCASpayload.text = "Released"
        elif int(MCASpayload) == 1:
            self.screens["mt"].ids.MCASpayload.text = "Captured"
        else:
            self.screens["mt"].ids.MCASpayload.text = "n/a"   
        #self.screens["mt"].ids.POApayload.text = str(POApayload)
        if int(POApayload) == 0:
            self.screens["mt"].ids.POApayload.text = "Released"
        elif int(POApayload) == 1:
            self.screens["mt"].ids.POApayload.text = "Captive"
        elif int(POApayload) == 2:
            self.screens["mt"].ids.POApayload.text = "Captured"
        else:
            self.screens["mt"].ids.POApayload.text = "n/a" 
        
        #self.screens["ssrms"].ids.OperatingBase.text = str(OperatingBase)
        if int(OperatingBase) == 0:
            self.screens["ssrms"].ids.OperatingBase.text = "A"
        elif int(OperatingBase) == 5:
            self.screens["ssrms"].ids.OperatingBase.text = "B"
        else:
            self.screens["ssrms"].ids.OperatingBase.text = "n/a"
                                      
        #self.screens["ssrms"].ids.TipLEEstatus.text = str(TipLEEstatus)
        if int(TipLEEstatus) == 0:
            self.screens["ssrms"].ids.TipLEEstatus.text = "Released"
        elif int(TipLEEstatus) == 1:
            self.screens["ssrms"].ids.TipLEEstatus.text = "Captive"
        elif int(TipLEEstatus) == 2:
            self.screens["ssrms"].ids.TipLEEstatus.text = "Captured"
        else:
            self.screens["ssrms"].ids.TipLEEstatus.text = "n/a"
        
         #self.screens["ssrms"].ids.SACSopBase.text = str(SACSopBase)
        if int(SACSopBase) == 0:
            self.screens["ssrms"].ids.SACSopBase.text = "A"
        elif int(SACSopBase) == 5:
            self.screens["ssrms"].ids.SACSopBase.text = "B"
        else:
            self.screens["ssrms"].ids.OperatingBase.text = "n/a"
        
        self.screens["ssrms"].ids.ShoulderRoll.text = str(ShoulderRoll) + " deg"
        self.screens["ssrms"].ids.ShoulderYaw.text = str(ShoulderYaw) + " deg"
        self.screens["ssrms"].ids.ShoulderPitch.text = str(ShoulderPitch) + " deg"
        self.screens["ssrms"].ids.ElbowPitch.text = str(ElbowPitch) + " deg"
        self.screens["ssrms"].ids.WristRoll.text = str(WristRoll) + " deg"
        self.screens["ssrms"].ids.WristYaw.text = str(WristYaw) + " deg"
        self.screens["ssrms"].ids.WristPitch.text = str(WristPitch) + " deg"
        
        #self.screens["ssrms"].ids.BaseLocation.text = str(BaseLocation)
        if int(BaseLocation) == 1:
            self.screens["ssrms"].ids.BaseLocation.text = "Lab"
        elif int(BaseLocation) == 2:
            self.screens["ssrms"].ids.BaseLocation.text = "Node 3"
        elif int(BaseLocation) == 4:
            self.screens["ssrms"].ids.BaseLocation.text = "Node 2"
        elif int(BaseLocation) == 7:
            self.screens["ssrms"].ids.BaseLocation.text = "MBS PDGF 1"
        elif int(BaseLocation) == 8:
            self.screens["ssrms"].ids.BaseLocation.text = "MBS PDGF 2"
        elif int(BaseLocation) == 11:
            self.screens["ssrms"].ids.BaseLocation.text = "MBS PDGF 3"
        elif int(BaseLocation) == 13:
            self.screens["ssrms"].ids.BaseLocation.text = "MBS PDGF 4"
        elif int(BaseLocation) ==14:
            self.screens["ssrms"].ids.BaseLocation.text = "FGB"
        elif int(BaseLocation) == 16:
            self.screens["ssrms"].ids.BaseLocation.text = "POA"
        elif int(BaseLocation) == 19:
            self.screens["ssrms"].ids.BaseLocation.text = "SSRMS Tip LEE"
        elif int(BaseLocation) == 63:
            self.screens["ssrms"].ids.BaseLocation.text = "Undefined"
        else:
            self.screens["ssrms"].ids.BaseLocation.text = "n/a"
        
        #self.screens["spdm"].ids.SPDMbase.text = str(SPDMbase)
        if int(SPDMbase) == 1:
            self.screens["spdm"].ids.SPDMbase.text = "Lab"
        elif int(SPDMbase) == 2:
            self.screens["spdm"].ids.SPDMbase.text = "Node 3"
        elif int(SPDMbase) == 4:
            self.screens["spdm"].ids.SPDMbase.text = "Node 2"
        elif int(SPDMbase) == 7:
            self.screens["spdm"].ids.SPDMbase.text = "MBS PDGF 1"
        elif int(SPDMbase) == 8:
            self.screens["spdm"].ids.SPDMbase.text = "MBS PDGF 2"
        elif int(SPDMbase) == 11:
            self.screens["spdm"].ids.SPDMbase.text = "MBS PDGF 3"
        elif int(SPDMbase) == 13:
            self.screens["spdm"].ids.SPDMbase.text = "MBS PDGF 4"
        elif int(SPDMbase) ==14:
            self.screens["spdm"].ids.SPDMbase.text = "FGB"
        elif int(SPDMbase) == 16:
            self.screens["spdm"].ids.SPDMbase.text = "POA"
        elif int(SPDMbase) == 19:
            self.screens["spdm"].ids.SPDMbase.text = "SSRMS Tip LEE"
        elif int(SPDMbase) == 63:
            self.screens["spdm"].ids.SPDMbase.text = "Undefined"
        else:
            self.screens["spdm"].ids.SPDMbase.text = "n/a"
        
         #self.screens["spdm"].ids.SPDMoperatingBase.text = str(SPDMoperatingBase)
        if int(SPDMoperatingBase) == 1:
            self.screens["spdm"].ids.SPDMoperatingBase.text = "SPDM Body LEE"
        elif int(SPDMoperatingBase) == 2:
            self.screens["spdm"].ids.SPDMoperatingBase.text = "SPDM Body PDGF"
        else:
            self.screens["spdm"].ids.SPDMoperatingBase.text = "n/a"
        
        #self.screens["spdm"].ids.Arm1OTCM.text = str(Arm1OTCM)
        if int(Arm1OTCM) == 0:
            self.screens["spdm"].ids.Arm1OTCM.text = "Released"
        elif int(Arm1OTCM) == 1:
            self.screens["spdm"].ids.Arm1OTCM.text = "Captive"
        elif int(Arm1OTCM) == 2:
            self.screens["spdm"].ids.Arm1OTCM.text = "Captured"
        else:
            self.screens["spdm"].ids.Arm1OTCM.text = "n/a"
        
        #self.screens["spdm"].ids.Arm2OTCM.text = str(Arm1OTCM)
        if int(Arm2OTCM) == 0:
            self.screens["spdm"].ids.Arm2OTCM.text = "Released"
        elif int(Arm2OTCM) == 1:
            self.screens["spdm"].ids.Arm2OTCM.text = "Captive"
        elif int(Arm2OTCM) == 2:
            self.screens["spdm"].ids.Arm2OTCM.text = "Captured"
        else:
            self.screens["spdm"].ids.Arm2OTCM.text = "n/a"
        
        #self.screens["spdm"].ids.BodyPayload.text = str(BodyPayload)
        if int(BodyPayload) == 0:
            self.screens["spdm"].ids.BodyPayload.text = "Released"
        elif int(BodyPayload) == 1:
            self.screens["spdm"].ids.BodyPayload.text = "Captive"
        elif int(BodyPayload) == 2:
            self.screens["spdm"].ids.BodyPayload.text = "Captured"
        else:
            self.screens["spdm"].ids.BodyPayload.text = "n/a"
        
        self.screens["spdm"].ids.BodyRoll.text = str(BodyRoll)
        self.screens["spdm"].ids.Shoulder1Roll.text = str(Shoulder1Roll)
        self.screens["spdm"].ids.Shoulder1Yaw.text = str(Shoulder1Yaw)
        self.screens["spdm"].ids.Shoulder1Pitch.text = str(Shoulder1Pitch)
        self.screens["spdm"].ids.Elbow1Pitch.text = str(Elbow1Pitch)
        self.screens["spdm"].ids.Wrist1Roll.text = str(Wrist1Roll)
        self.screens["spdm"].ids.Wrist1Yaw.text = str(Wrist1Yaw)
        self.screens["spdm"].ids.Wrist1Pitch.text = str(Wrist1Pitch)
        self.screens["spdm"].ids.Shoulder2Roll.text = str(Shoulder2Roll)
        self.screens["spdm"].ids.Shoulder2Yaw.text = str(Shoulder2Yaw)
        self.screens["spdm"].ids.Shoulder2Pitch.text = str(Shoulder2Pitch)
        self.screens["spdm"].ids.Elbow2Pitch.text = str(Elbow2Pitch)
        self.screens["spdm"].ids.Wrist2Roll.text = str(Wrist2Roll)
        self.screens["spdm"].ids.Wrist2Yaw.text = str(Wrist2Yaw)
        self.screens["spdm"].ids.Wrist2Pitch.text = str(Wrist2Pitch)

        self.screens["eva_emu"].ids.UIApowerEMU1.text = str(UIApowerEMU1) + " V"
        self.screens["eva_emu"].ids.UIApowerEMU2.text = str(UIApowerEMU2) + " V"
        self.screens["eva_emu"].ids.UIAcurrentEMU1.text = str(UIAcurrentEMU1) + " A"
        self.screens["eva_emu"].ids.UIAcurrentEMU2.text = str(UIAcurrentEMU2)  + " A" 
        self.screens["eva_emu"].ids.PSApowerEMU1.text = str(PSApowerEMU1) + " V"
        self.screens["eva_emu"].ids.PSApowerEMU2.text = str(PSApowerEMU2) + " V"
        self.screens["eva_emu"].ids.PSAcurrentEMU1.text = str(PSAcurrentEMU1) + " A"
        self.screens["eva_emu"].ids.PSAcurrentEMU2.text = str(PSAcurrentEMU2) + " A"
        self.screens["eva_emu"].ids.IRUvoltage.text = str(IRUvoltage) + " V"
        self.screens["eva_emu"].ids.IRUcurrent.text = str(IRUcurrent) + " A"
        
        #self.screens["ct_uhf"].ids.UHF1pwr.text = str(UHF1pwr)
        if int(UHF1pwr) == 0:
            self.screens["ct_uhf"].ids.UHF1pwr.text = "Off-Ok"
        elif int(UHF1pwr) == 1:
            self.screens["ct_uhf"].ids.UHF1pwr.text = "Not Off-Ok"
        elif int(UHF1pwr) == 2:
            self.screens["ct_uhf"].ids.UHF1pwr.text = "Not Off-Failed"
        else:
            self.screens["ct_uhf"].ids.UHF1pwr.text = "n/a"        
        #self.screens["ct_uhf"].ids.UHF2pwr.text = str(UHF2pwr)
        if int(UHF2pwr) == 0:
            self.screens["ct_uhf"].ids.UHF2pwr.text = "Off-Ok"
        elif int(UHF2pwr) == 1:
            self.screens["ct_uhf"].ids.UHF2pwr.text = "Not Off-Ok"
        elif int(UHF2pwr) == 2:
            self.screens["ct_uhf"].ids.UHF2pwr.text = "Not Off-Failed"
        else:
            self.screens["ct_uhf"].ids.UHF2pwr.text = "n/a"
        #self.screens["ct_uhf"].ids.UHFframeSync.text = str(UHFframeSync)
        if int(UHFframeSync) == 0:
            self.screens["ct_uhf"].ids.UHFframeSync.text = "Unlocked"
        elif int(UHFframeSync) == 1:
            self.screens["ct_uhf"].ids.UHFframeSync.text = "Locked"
        else:
            self.screens["iss"].ids.UHFframeSync.text = "n/a"

            self.screens["ct_sgant"].ids.sgant_transmit.text = str(sgant_transmit)
        if int(sgant_transmit) == 0:
            self.screens["ct_sgant"].ids.sgant_transmit.text = "RESET"
        elif int(sgant_transmit) == 1:
            self.screens["ct_sgant"].ids.sgant_transmit.text = "NORMAL"
        else:
            self.screens["ct_sgant"].ids.sgant_transmit.text = "n/a"
        
        self.screens["ct_sasa"].ids.ActiveString.text = str(ActiveString)
        self.screens["ct_sasa"].ids.RFG1status.text = str(RFG1status)
        if int(RFG1status) == 0:
            self.screens["ct_sasa"].ids.RFG1status.text = "Off-Ok"
        elif int(RFG1status) == 1:
            self.screens["ct_sasa"].ids.RFG1status.text = "Not Off-Ok"
        elif int(RFG1status) == 2:
            self.screens["ct_sasa"].ids.RFG1status.text = "Not Off-Failed"
        else:
            self.screens["ct_sasa"].ids.RFG1status.text = "n/a"
        self.screens["ct_sasa"].ids.RFG1azimuth.text = str(RFG1azimuth)
        self.screens["ct_sasa"].ids.RFG1elev.text = str(RFG1elev)
        
        self.screens["ct_sasa"].ids.RFG2status.text = str(RFG2status)
        if int(RFG2status) == 0:
            self.screens["ct_sasa"].ids.RFG2status.text = "Off-Ok"
        elif int(RFG2status) == 1:
            self.screens["ct_sasa"].ids.RFG2status.text = "Not Off-Ok"
        elif int(RFG2status) == 2:
            self.screens["ct_sasa"].ids.RFG2status.text = "Not Off-Failed"
        else:
            self.screens["ct_sasa"].ids.RFG2status.text = "n/a"
        self.screens["ct_sasa"].ids.RFG2azimuth.text = str(RFG2azimuth)
        self.screens["ct_sasa"].ids.RFG2elev.text = str(RFG2elev)        

        self.screens["eps"].ids.beta1b_value.text = beta1b
        self.screens["eps"].ids.beta1a_value.text = beta1a
        self.screens["eps"].ids.beta2b_value.text = beta2b
        self.screens["eps"].ids.beta2a_value.text = beta2a
        self.screens["eps"].ids.beta3b_value.text = beta3b
        self.screens["eps"].ids.beta3a_value.text = beta3a
        self.screens["eps"].ids.beta4b_value.text = beta4b
        self.screens["eps"].ids.beta4a_value.text = beta4a
        self.screens["eps"].ids.c1a_value.text = c1a + "A"
        self.screens["eps"].ids.v1a_value.text = v1a + "V"
        self.screens["eps"].ids.c1b_value.text = c1b + "A"
        self.screens["eps"].ids.v1b_value.text = v1b + "V"
        self.screens["eps"].ids.c2a_value.text = c2a + "A"
        self.screens["eps"].ids.v2a_value.text = v2a + "V"
        self.screens["eps"].ids.c2b_value.text = c2b + "A"
        self.screens["eps"].ids.v2b_value.text = v2b + "V"
        self.screens["eps"].ids.c3a_value.text = c3a + "A"
        self.screens["eps"].ids.v3a_value.text = v3a + "V"
        self.screens["eps"].ids.c3b_value.text = c3b + "A"
        self.screens["eps"].ids.v3b_value.text = v3b + "V"
        self.screens["eps"].ids.c4a_value.text = c4a + "A"
        self.screens["eps"].ids.v4a_value.text = v4a + "V"
        self.screens["eps"].ids.c4b_value.text = c4b + "A"
        self.screens["eps"].ids.v4b_value.text = v4b + "V"
        self.screens["iss"].ids.altitude_value.text = str(altitude) + " km"

        self.screens["iss"].ids.velocity_value.text = str(velocity) + " km/s"
        self.screens["iss"].ids.stationmass_value.text = str(iss_mass) + " kg"

        self.screens["us_eva"].ids.EVA_needle.angle = float(self.map_rotation(0.0193368*float(crewlockpres)))
        self.screens["us_eva"].ids.crewlockpressure_value.text = "{:.2f}".format(0.0193368*float(crewlockpres))

        psi_bar_x = self.map_psi_bar(0.0193368*float(crewlockpres)) #convert to torr

        self.screens["us_eva"].ids.EVA_psi_bar.pos_hint = {"center_x": psi_bar_x, "center_y": 0.61}


        ##-------------------Signal Status Check-------------------##

        #if client_status.split(":")[0] == "CONNECTED": we dont check client status anymore in the python lightstreamer script
        if sub_status == "Subscribed":
            #client connected and subscibed to ISS telemetry
            if float(aos) == 1.00:
                self.signal_acquired() #signal status 1 means acquired
                sasa_xmit = 1
            elif float(aos) == 0.00:
               self.signal_lost() #signal status 0 means loss of signal
               sasa_xmit = 0
            elif float(aos) == 2.00:
               self.signal_stale() #signal status 2 means data is not being updated from server
               sasa_xmit = 0
        else:
            self.signal_unsubscribed()
        #else:
        #    self.signal_unsubscribed()

        if mimicbutton: # and float(aos) == 1.00):
            serialWrite("PSARJ=" + psarj + " " + "SSARJ=" + ssarj + " " + "PTRRJ=" + ptrrj + " " + "STRRJ=" + strrj + " " + "B1B=" + beta1b + " " + "B1A=" + beta1a + " " + "B2B=" + beta2b + " " + "B2A=" + beta2a + " " + "B3B=" + beta3b + " " + "B3A=" + beta3a + " " + "B4B=" + beta4b + " " + "B4A=" + beta4a + " " + "AOS=" + aos + " " + "V1A=" + str(v1as) + " " + "V2A=" + str(v2as) + " " + "V3A=" + str(v3as) + " " + "V4A=" + str(v4as) + " " + "V1B=" + str(v1bs) + " " + "V2B=" + str(v2bs) + " " + "V3B=" + str(v3bs) + " " + "V4B=" + str(v4bs) + " " + "ISS=" + module + " " + "Sgnt_el=" + str(int(sgant_elevation)) + " " + "Sgnt_xel=" + str(int(sgant_xelevation)) + " " + "Sgnt_xmit=" + str(int(sgant_transmit)) + " " + "SASA_Xmit=" + str(int(sasa_xmit)) + " SASA_AZ=" + str(float(sasa_az)) + " SASA_EL=" + str(float(sasa_el)) + " ")

if __name__ == '__main__':
    MainApp().run()
