#!/usr/bin/env python3

import argparse
import sys
import os
import traceback

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
    #print("Debug logging enabled - INFO level and above will be logged")
elif args.quiet:
    os.environ['MIMIC_LOG_LEVEL'] = 'CRITICAL'
    #print("Quiet mode enabled - only critical errors will be logged")
else:
    os.environ['MIMIC_LOG_LEVEL'] = 'ERROR'
    #print("Normal mode - ERROR level and above will be logged")

if args.console_logging:
    os.environ['MIMIC_CONSOLE_LOGGING'] = '1'
    #print("Console logging enabled")

# Now import the rest of the modules
import os.path as op

import os # used to remove database on program exit; also used for importing config.json
os.environ["KIVY_NO_CONSOLELOG"] = "1"   # Kivy: no automatic console handler
os.environ["KIVY_LOG_LEVEL"]    = "error"  # (< INFO is ignored without handler,

from datetime import datetime, timedelta #used for time conversions and logging timestamps
from dateutil.relativedelta import relativedelta
import datetime as dtime #this is different from above for... reasons?
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

import Screens as screens
from utils.logger import log_info, log_error

mimic_data_directory = Path.home() / '.mimic_data'
mimic_directory = op.abspath(op.join(__file__, op.pardir, op.pardir, op.pardir))

# Constants
SERIAL_SPEED = 9600

os.environ['KIVY_GL_BACKEND'] = 'gl' #need this to fix a kivy segfault that occurs with python3 for some reason

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
        log_error(f"Warning: Could not enumerate TTY devices: {e}")
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
    log_info("No serial ports available")

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

    mimicbutton = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.internet: bool | None = None # None = "unknown"

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
            Clock.schedule_interval(self.update_signal_status, 1) #all telemetry wil refresh and get pushed to arduinos every half second!
            Clock.schedule_interval(self.updateArduinoCount, 5) #update arduino count every 5 seconds
            Clock.schedule_interval(self._schedule_internet_probe,
                                    self.INTERNET_POLL_S) # check for active internet connection

            log_info("All functions scheduled")
            log_info("Build process completed successfully")
            return root
            
        except Exception as e:
            log_error(f"Error during build: {e}")
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


    def set_mimic_transmission_status(self, is_transmitting: bool) -> None:
        """
        Called by mimic screen to inform GUI.py about transmission status.
        This allows GUI.py to update Arduino animations across all screens.
        """
        try:
            # Update the mimic button status
            self.mimicbutton = is_transmitting
            
            # Force an immediate Arduino count update to show transmit animation
            self.updateArduinoCount(0)
            
            log_info(f"Mimic transmission status set to: {is_transmitting}")
            
        except Exception as exc:
            log_error(f"Failed to set mimic transmission status: {exc}")

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
        arduino_count = (
            len(getattr(self, "serial_ports", []))
            if hasattr(self, "serial_ports")
            else len(SERIAL_PORTS)         # ? existing global
        )

        # Get mimic transmission status
        mimic_is_tx = (
            getattr(self, "mimicbutton", False)
            if hasattr(self, "mimicbutton")
            else False
        )

        """
        Refresh the Arduino-status icon & counter on screens that have them.
        Skip screens that have local animation control.
        """
        
        # Screens that should have local animation control (don't override)
        local_control_screens = {'manualcontrol', 'led', 'playback', 'main'}
        
        for scr in self.screens.values():
            ids = scr.ids

            # Skip screens without the widgets.
            if "arduino_count" not in ids or "arduino" not in ids:
                continue
                
            # Skip screens that have local animation control
            if scr.name in local_control_screens:
                # Only update the count, not the animation source
                if arduino_count > 0:
                    ids.arduino_count.text = str(arduino_count)
                else:
                    ids.arduino_count.text = ""
                continue

            # For other screens, update both count and animation
            if arduino_count > 0:
                ids.arduino_count.text = str(arduino_count)
                new_source = (
                    f"{self.mimic_directory}/Mimic/Pi/imgs/signal/"
                    + ("arduino_transmit.zip" if mimic_is_tx
                       else "arduino_notransmit.png")
                )
                ids.arduino.source = new_source
            else:
                ids.arduino_count.text = ""
                offline_source = f"{self.mimic_directory}/Mimic/Pi/imgs/signal/arduino_offline.png"
                ids.arduino.source = offline_source

    
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
            log_info("Signal unsubscribed, internet offline")
        else:
            self._broadcast_signal("SignalClientLost.png", (1, 0.5, 0))
            log_info("Signal unsubscribed, internet online")

    def signal_lost(self):
        if not self.internet:
            self._broadcast_signal("offline.png", (0.5, 0.5, 0.5))
            log_info("Signal lost, internet offline")
        else:
            self._broadcast_signal("signalred.zip", (1, 0, 0), anim_delay=0.4)
            log_info("Signal lost, internet online")

    def signal_acquired(self):
        if not self.internet:
            self._broadcast_signal("offline.png", (0.5, 0.5, 0.5))
            #log_info("Signal acquired, internet offline")
        else:
            self._broadcast_signal("pulse-transparent.zip", (0, 1, 0),
                                   anim_delay=0.05, size_hint_y=0.15)
            #log_info("Signal acquired, internet online")

    def signal_stale(self):
        if not self.internet:
            self._broadcast_signal("offline.png", (0.5, 0.5, 0.5))
            #log_info("Signal stale, internet offline")
        else:
            self._broadcast_signal("SignalOrangeGray.png", (1, 0.5, 0),
                                   anim_delay=0.12)
            #log_info("Signal stale, internet online")

    def signal_client_offline(self):
        if not self.internet:
            self._broadcast_signal("offline.png", (0.5, 0.5, 0.5))
            #log_info("Signal client offline, internet offline")
        else:
            self._broadcast_signal("SignalClientLost.png", (1, 0.5, 0),
                                   anim_delay=0.12)
            #log_info("Signal client offline, internet online")

    def update_signal_status(self, dt):
        """
        Update the signal status on all screens.
        - Reads only the needed telemetry rows by label.
        - Avoids relying on implicit SQLite row ordering.
        - Compares AOS numerically.
        """
        try:
            # Fetch Lightstreamer and AOS directly by label
            c.execute("SELECT Value FROM telemetry WHERE Label = 'Lightstreamer'")
            row = c.fetchone()
            if not row:
                log_error("Lightstreamer status not found in telemetry table")
                return
            sub_status = str(row[0])

            c.execute("SELECT Value, Timestamp FROM telemetry WHERE Label = 'aos'")
            row = c.fetchone()
            if not row:
                log_error("AOS not found in telemetry table")
                return

            # iss_telemetry writes 0/1/2 here
            aos_val = int(float(row[0]))  # robust if stored as '0', '0.0', etc.

        except Exception as e:
            log_error(f"Error getting telemetry values: {e}")
            return

        # Only react when we’re actually subscribed
        if sub_status == "Subscribed":
            # Map AOS state to the right visual
            if aos_val == 1:
                self.signal_acquired()
            elif aos_val == 0:
                self.signal_lost()
            elif aos_val == 2:
                self.signal_stale()
        else:
            self.signal_unsubscribed()


if __name__ == '__main__':
    try:
        # Show logging configuration
        log_level = os.environ.get('MIMIC_LOG_LEVEL', 'ERROR')
        console_enabled = os.environ.get('MIMIC_CONSOLE_LOGGING', '0') == '1'
        log_info("--------------------------------")
        log_info("Initialized Mimic Program")
        print(f"=== ISS Mimic GUI ===")
        print(f"Logging Level: {log_level}")
        print(f"Console Logging: {'Enabled' if console_enabled else 'Disabled'}")
        print(f"Log File: ~/Mimic/Pi/Logs/mimic.log")
        print("Mimic Program Directory: " + mimic_directory + "/Mimic/Pi")
        print("Mimic Data Directory: " + str(mimic_data_directory))
        print("run: \"python GUI.py --debug\" to enable debug logging")
        print(f"=====================")
        
        import database_initialize # create and populate database script
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
        traceback.print_exc()
        
        # Keep the console open so the user can see the error
        input("Press Enter to exit...")
