#!/usr/bin/env python3

import argparse
import sys
import os

# Parse command line arguments first, before any other imports
def parse_arguments():
    parser = argparse.ArgumentParser(description='ISS Mimic GUI Application')
    parser.add_argument('--debug', action='store_true', 
                       help='Enable debug logging (INFO level)')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging (INFO level) - same as --debug')
    parser.add_argument('--quiet', action='store_true',
                       help='Suppress all logging output')
    parser.add_argument('--console-logging', action='store_true',
                       help='Enable console logging in addition to file logging')
    
    return parser.parse_args()

# Parse arguments and set environment variables for logger configuration
args = parse_arguments()

if args.debug or args.verbose:
    os.environ['MIMIC_LOG_LEVEL'] = 'INFO'
    print("Debug logging enabled - INFO level and above will be logged")
elif args.quiet:
    os.environ['MIMIC_LOG_LEVEL'] = 'CRITICAL'
    print("Quiet mode enabled - only critical errors will be logged")
else:
    os.environ['MIMIC_LOG_LEVEL'] = 'ERROR'
    print("Normal mode - ERROR level and above will be logged")

if args.console_logging:
    os.environ['MIMIC_CONSOLE_LOGGING'] = '1'
    print("Console logging enabled")

# Now import the rest of the modules
import os.path as op

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
import argparse
import sys
import os.path as op #use for getting mimic directory
from pathlib import Path
import pathlib, sys, signal
import math
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Conditional import for pyudev (Linux only)
try:
    from pyudev import Context, Devices, Monitor, MonitorObserver # for automatically detecting Arduinos - not available on Windows
    PYUDEV_AVAILABLE = True
except ImportError:
    PYUDEV_AVAILABLE = False
    # Create dummy classes for Windows
    class Context: pass
    class Devices: pass
    class Monitor: pass
    class MonitorObserver: pass

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

# Global variables for animations and arduino count
new_x = 0.0
new_y = 0.75
sizeX = 0.07
sizeY = 0.07
startingAnim = True
new_x2 = 0.0
new_y2 = 0.75
mimicbutton = False
demoboolean = False
runningDemo = False
Disco = False

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
    if not PYUDEV_AVAILABLE:
        # Return empty list on Windows where pyudev is not available
        return []
    
    names = []
    try:
        devices = context.list_devices(subsystem='tty')
        for d in devices:
            for k, v in d.items():
                # Check for both ID_VENDOR and ID_USB_VENDOR
                if k in ['ID_VENDOR', 'ID_USB_VENDOR']:
                    names.append(parse_tty_name(d, v))
    except Exception as e:
        print(f"Warning: Could not enumerate TTY devices: {e}")
        return []
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
if not USE_CONFIG_JSON and PYUDEV_AVAILABLE:
    MONITOR = Monitor.from_netlink(context)
    TTY_OBSERVER = MonitorObserver(MONITOR, callback=detect_device_event, name='monitor-observer')
    TTY_OBSERVER.daemon = False
else:
    MONITOR = None
    TTY_OBSERVER = None

SERIAL_PORTS = get_serial_ports(context, USE_CONFIG_JSON)
OPEN_SERIAL_PORTS = []

# Only try to open serial ports if we have any
if SERIAL_PORTS:
    try:
        open_serial_ports(SERIAL_PORTS)
        log_str = "Serial ports opened: " + str(SERIAL_PORTS)
        log_info(log_str)
    except Exception as e:
        log_error(f"Could not open serial ports: {e}")
        SERIAL_PORTS = []
        OPEN_SERIAL_PORTS = []
else:
    log_info("No serial ports available (this is normal on Windows)")

if not USE_CONFIG_JSON and PYUDEV_AVAILABLE and TTY_OBSERVER:
    TTY_OBSERVER.start()
    log_str = "Started monitoring serial ports."
    log_info(log_str)
    log_info(log_str)

#-----------------------------Checking Databases-----------------------------------------
# Cross-platform database path handling
def get_db_path(db_name):
    """Get database path with cross-platform handling."""
    shm = pathlib.Path(f'/dev/shm/{db_name}')
    if shm.exists():
        return str(shm)
    return str(pathlib.Path.home() / '.mimic_data' / db_name)

TDRSconn = sqlite3.connect(get_db_path('tdrs.db'))
TDRSconn.isolation_level = None
TDRScursor = TDRSconn.cursor()
VVconn = sqlite3.connect(get_db_path('vv.db'))
VVconn.isolation_level = None
VVcursor = VVconn.cursor()
conn = sqlite3.connect(get_db_path('iss_telemetry.db'))
conn.isolation_level = None
c = conn.cursor()

def staleTelemetry():
    c.execute("UPDATE telemetry SET Value = 'Unsubscribed' where Label = 'Lightstreamer'")
#----------------------------------Variables---------------------------------------------

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
    mimicbutton = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.internet: bool | None = None # None = "unknown"

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
        
        # Bind mimicbutton property to update global variable
        self.bind(mimicbutton=self._on_mimicbutton_change)
    
    def _on_mimicbutton_change(self, instance, value):
        """Update global mimicbutton variable when app property changes."""
        global mimicbutton
        mimicbutton = value

    def build(self):
        try:
            log_info("Starting build process...")
            # 1. instantiate once, store in a dict
            log_info("Creating screens...")
            self.screens = {}
            for sid, cls in SCREEN_DEFS.items():
                try:
                    log_info(f"Creating screen: {sid}")
                    screen = cls(name=sid)
                    self.screens[sid] = screen
                    log_info(f"Successfully created screen: {sid}")
                except Exception as e:
                    log_error(f"Error creating screen {sid}: {e}")
                    import traceback
                    traceback.print_exc()
                    # Continue with other screens instead of crashing
                    continue
            log_info(f"Created {len(self.screens)} screens")

            # 2. ScreenManager wiring
            log_info("Creating screen manager...")
            root = MainScreenManager(transition=NoTransition())
            log_info("Adding screens to manager...")
            for sid, scr in self.screens.items():
                try:
                    log_info(f"Adding screen {sid} to manager...")
                    root.add_widget(scr)
                    log_info(f"Successfully added screen {sid} to manager")
                except Exception as e:
                    log_error(f"Error adding screen {sid} to manager: {e}")
                    import traceback
                    traceback.print_exc()
                    # Continue with other screens instead of crashing
                    continue
            log_info("All screens added")
            
            if not self.screens:
                log_error("No screens were created successfully!")
                raise Exception("No screens available")
                
            root.current = "main"
            log_info("Set current screen to main")

            log_info("Scheduling update functions...")
            Clock.schedule_interval(self.update_labels, 1) #all telemetry wil refresh and get pushed to arduinos every half second!
            Clock.schedule_interval(self.animate3, 0.1)
            #Clock.schedule_interval(self.checkCrew, 600) #disabling for now issue #407
            #Clock.schedule_once(self.checkCrew, 30) #disabling for now issue #407

            Clock.schedule_interval(self._schedule_internet_probe,
                                    self.INTERNET_POLL_S) # check for active internet connection

            Clock.schedule_interval(self.updateArduinoCount, 5)
            log_info("All functions scheduled")

            log_info("Build process completed successfully")
            return root
            
        except Exception as e:
            log_error(f"Error during build: {e}")
            import traceback
            traceback.print_exc()
            # Return a simple error screen instead of crashing
            from kivy.uix.label import Label
            error_label = Label(text=f'Error loading application:\n{str(e)}')
            return error_label

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
                    + ("Arduino_Transmit.zip" if mimic_is_tx
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
            if mimic_is_tx:
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


    def update_labels(self, dt): #THIS IS THE IMPORTANT FUNCTION
        global mimicbutton, demoboolean, runningDemo, Disco

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
        ssarj = "{:.2f}".format(float((values[1])[0]))
        ptrrj = "{:.2f}".format(float((values[2])[0]))
        strrj = "{:.2f}".format(float((values[3])[0]))
        beta1b = "{:.2f}".format(float((values[4])[0]))
        beta1a = "{:.2f}".format(float((values[5])[0]))
        beta2b = "{:.2f}".format(float((values[6])[0]))
        beta2a = "{:.2f}".format(float((values[7])[0]))
        beta3b = "{:.2f}".format(float((values[8])[0]))
        beta3a = "{:.2f}".format(float((values[9])[0]))
        beta4b = "{:.2f}".format(float((values[10])[0]))
        beta4a = "{:.2f}".format(float((values[11])[0]))

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

        # array status numbers to be sent to arduino
        # 1 = discharging
        # 2 = charging
        # 3 = full
        # 4 = offline

        if float(v1a) < 151.5: #discharging
            v1as = 1
        elif float(v1a) > 160.0: #charged
            v1as = 3
        elif float(v1a) >= 151.5:  #charging
            v1as = 2
        if float(c1a) > 0.0:    #power channel offline!
            v1as = 4

        if float(v1b) < 151.5: #discharging
            v1bs = 1
        elif float(v1b) > 160.0: #charged
            v1bs = 3
        elif float(v1b) >= 151.5:  #charging
            v1bs = 2
        if float(c1b) > 0.0:                                  #power channel offline!
            v1bs = 4

        if float(v2a) < 151.5: #discharging
            v2as = 1
        elif float(v2a) > 160.0: #charged
            v2as = 3
        elif float(v2a) >= 151.5:  #charging
            v2as = 2
        if float(c2a) > 0.0:                                  #power channel offline!
            v2as = 4

        if float(v2b) < 151.5: #discharging
            v2bs = 1
        elif float(v2b) > 160.0: #charged
            v2bs = 3
        elif float(v2b) >= 151.5:  #charging
            v2bs = 2
        if float(c2b) > 0.0:                                  #power channel offline!
            v2bs = 4

        if float(v3a) < 151.5: #discharging
            v3as = 1
        elif float(v3a) > 160.0: #charged
            v3as = 3
        elif float(v3a) >= 151.5:  #charging
            v3as = 2
        if float(c3a) > 0.0:                                  #power channel offline!
            v3as = 4

        if float(v3b) < 151.5: #discharging
            v3bs = 1
        elif float(v3b) > 160.0: #charged
            v3bs = 3
        elif float(v3b) >= 151.5:  #charging
            v3bs = 2
        if float(c3b) > 0.0:                                  #power channel offline!
            v3bs = 4

        if float(v4a) < 151.5: #discharging
            v4as = 1
        elif float(v4a) > 160.0: #charged
            v4as = 3
        elif float(v4a) >= 151.5:  #charging
            v4as = 2
        if float(c4a) > 0.0:                                  #power channel offline!
            v4as = 4
        
        if float(v4b) < 151.5: #discharging
            v4bs = 1
        elif float(v4b) > 160.0: #charged
            v4bs = 3
        elif float(v4b) >= 151.5:  #charging
            v4bs = 2
        if float(c4b) > 0.0:                                  #power channel offline!
            v4bs = 4

        sgant_elevation = float((values[15])[0])
        sgant_xelevation = float((values[17])[0])
        sgant_transmit = float((values[41])[0])

        if demoboolean:
            if Disco:
                serialWrite("Disco ")
                Disco = False
            serialWrite("PSARJ=" + psarj + " " + "SSARJ=" + ssarj + " " + "PTRRJ=" + ptrrj + " " + "STRRJ=" + strrj + " " + "B1B=" + beta1b + " " + "B1A=" + beta1a + " " + "B2B=" + beta2b + " " + "B2A=" + beta2a + " " + "B3B=" + beta3b + " " + "B3A=" + beta3a + " " + "B4B=" + beta4b + " " + "B4A=" + beta4a + " " + "AOS=" + aos + " " + "V1A=" + str(v1as) + " " + "V2A=" + str(v2as) + " " + "V3A=" + str(v3as) + " " + "V4A=" + str(v4as) + " " + "V1B=" + str(v1bs) + " " + "V2B=" + str(v2bs) + " " + "V3B=" + str(v3bs) + " " + "V4B=" + str(v4bs) + " " + "Sgnt_el=" + str(int(sgant_elevation)) + " " + "Sgnt_xel=" + str(int(sgant_xelevation)) + " " + "Sgnt_xmit=" + str(int(sgant_transmit)) + " " + "SASA_Xmit=" + str(int(sasa_xmit)) + " SASA_AZ=" + str(float(sasa_az)) + " SASA_EL=" + str(float(sasa_el)) + " ")

        
        #UHF telemetry updates now handled in CT_UHF_Screen


        # ISS telemetry updates moved to ISS_Screen

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


        if mimicbutton: # and float(aos) == 1.00):
            serialWrite("PSARJ=" + psarj + " " + "SSARJ=" + ssarj + " " + "PTRRJ=" + ptrrj + " " + "STRRJ=" + strrj + " " + "B1B=" + beta1b + " " + "B1A=" + beta1a + " " + "B2B=" + beta2b + " " + "B2A=" + beta2a + " " + "B3B=" + beta3b + " " + "B3A=" + beta3a + " " + "B4B=" + beta4b + " " + "B4A=" + beta4a + " " + "AOS=" + aos + " " + "V1A=" + str(v1as) + " " + "V2A=" + str(v2as) + " " + "V3A=" + str(v3as) + " " + "V4A=" + str(v4as) + " " + "V1B=" + str(v1bs) + " " + "V2B=" + str(v2bs) + " " + "V3B=" + str(v3bs) + " " + "V4B=" + str(v4bs) + " " + "Sgnt_el=" + str(int(sgant_elevation)) + " " + "Sgnt_xel=" + str(int(sgant_xelevation)) + " " + "Sgnt_xmit=" + str(int(sgant_transmit)) + " " + "SASA_Xmit=" + str(int(sasa_xmit)) + " SASA_AZ=" + str(float(sasa_az)) + " SASA_EL=" + str(float(sasa_el)) + " ")

if __name__ == '__main__':
    try:
        # Show logging configuration
        log_level = os.environ.get('MIMIC_LOG_LEVEL', 'ERROR')
        console_enabled = os.environ.get('MIMIC_CONSOLE_LOGGING', '0') == '1'
        print(f"=== ISS Mimic GUI ===")
        print(f"Logging Level: {log_level}")
        print(f"Console Logging: {'Enabled' if console_enabled else 'Disabled'}")
        print(f"Log File: ~/Mimic/Pi/Logs/mimic.log")
        print(f"=====================")
        
        log_info("Starting ISS Mimic Program")
        log_info("Mimic Program Directory: " + mimic_directory + "/Mimic/Pi")
        log_info("Mimic Data Directory: " + str(mimic_data_directory))
        
        # Create the app and run it
        app = MainApp()
        log_info("MainApp created successfully")
        app.run()
        log_info("Application finished normally")
        
    except Exception as e:
        log_error(f"Fatal error during startup: {e}")
        import traceback
        traceback.print_exc()
        
        # Keep the console open so the user can see the error
        input("Press Enter to exit...")
