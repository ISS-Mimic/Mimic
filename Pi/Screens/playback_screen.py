from __future__ import annotations

import pathlib
import time
import threading
from pathlib import Path
from typing import Optional, Dict, Any

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.spinner import Spinner
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.app import App
from kivy.uix.screenmanager import Screen
from subprocess import Popen, TimeoutExpired

from ._base import MimicBase
from utils.logger import log_info, log_error
from utils.serial import serialWrite

# ── load KV next to this file ──────────────────────────────────────────────
kv_path = pathlib.Path(__file__).with_name("Playback_Screen.kv")
Builder.load_file(str(kv_path))

# ───────────────────────────────────────────────────────────────────────────
class Playback_Screen(MimicBase):
    """
    Clean, simple playback screen for recorded ISS telemetry data.
    """

    # Playback state
    is_playing = BooleanProperty(False)
    current_file = StringProperty("")
    playback_speed = NumericProperty(0)  # Changed from 10.0 to 0 (no default)
    
    # Arduino connection status
    arduino_connected = BooleanProperty(False)
    loop_enabled = BooleanProperty(False)
    
    # Playback data
    _playback_data = []
    _current_index = 0
    _playback_timer = None
    
    # Serial writing
    _serial_timer = None
    _serial_update_interval = 0.1  # Update every 100ms (10Hz)
    
    # LED control
    _disco_colors = ["Red", "Green", "Blue", "Yellow", "Purple", "Cyan", "White", "Orange"]

    def __init__(self, **kw):
        super().__init__(**kw)
        
        # Start monitoring Arduino connection
        Clock.schedule_interval(self._check_arduino_connection, 5.0)
        
        # Start monitoring USB drives
        self._start_usb_monitor()

    # ---------------------------------------------------------------- Arduino Check
    def _check_arduino_connection(self, dt):
        """Check if Arduino is connected by checking the arduino count text."""
        try:
            # Get arduino count from the screen's own arduino_count label
            # This gets updated by the main app's updateArduinoCount method
            arduino_count_label = getattr(self.ids, 'arduino_count', None)
            if arduino_count_label:
                arduino_count_text = arduino_count_label.text.strip()
                if arduino_count_text and arduino_count_text.isdigit():
                    arduino_count = int(arduino_count_text)
                    self.arduino_connected = arduino_count > 0
                else:
                    self.arduino_connected = False
            else:
                self.arduino_connected = False
                
        except Exception as e:
            log_error(f"Error checking Arduino connection: {e}")
            self.arduino_connected = False
        
        # Check start button state whenever Arduino connection changes
        self._check_start_button_state()

    # ---------------------------------------------------------------- USB Monitoring
    def _start_usb_monitor(self):
        """Start background thread to monitor USB drives."""
        def monitor_loop():
            while True:
                try:
                    self._scan_usb_drives()
                    time.sleep(5)  # Check every 5 seconds
                except Exception as e:
                    log_error(f"USB monitoring error: {e}")
                    time.sleep(10)  # Longer delay on error
        
        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()

    def _scan_usb_drives(self):
        """Scan for USB drives and update dropdown."""
        try:
            media_dir = Path("/media/pi")
            if not media_dir.exists():
                return
                
            drives = [d.name for d in media_dir.iterdir() if d.is_dir()]
            
            # Update dropdown on main thread
            Clock.schedule_once(lambda dt: self._update_dropdown(drives))
            
        except Exception as e:
            log_error(f"USB scan failed: {e}")

    def _update_dropdown(self, drives):
        """Update the file selection dropdown."""
        try:
            dropdown = self.ids.file_dropdown
            if dropdown:
                # Add USB drives
                usb_files = [f"{d} (USB)" for d in sorted(drives)]
                
                # Add built-in demos
                builtin_demos = ["HTV", "OFT2", "Standard"]
                
                dropdown.values = usb_files + builtin_demos
                
        except Exception as e:
            log_error(f"Error updating dropdown: {e}")

    # ---------------------------------------------------------------- File Selection
    def on_dropdown_select_data(self, filename):
        """Called when user selects a file from dropdown and close it."""
        if not filename:
            return
            
        log_info(f"File selected: {filename}")
        
        # Parse the selection
        if "(USB)" in filename:
            # USB drive file
            drive_name = filename.replace(" (USB)", "")
            self._load_usb_file(drive_name)
        else:
            # Built-in demo
            self._load_builtin_demo(filename)
        
 
        
        # Update status and check if start button should be enabled
        self._update_status()
        self._check_start_button_state()

    def _load_usb_file(self, drive_name: str):
        """Load playback data from USB drive."""
        try:
            # Look for data folders (not CSV files anymore)
            usb_path = Path(f"/media/pi/{drive_name}")
            
            # Find data folders (like HTV, OFT2, etc.)
            data_folders = [d.name for d in usb_path.iterdir() if d.is_dir()]
            
            if not data_folders:
                self._show_error("No data folders found on USB drive")
                return
                
            # For now, just show the first folder found
            # Later we can add folder selection
            self.current_file = f"{drive_name} (USB)"
            log_info(f"Loaded USB data folder: {data_folders[0]}")
            
        except Exception as e:
            log_error(f"Error loading USB file: {e}")
            self._show_error(f"Error loading USB file: {e}")

    def _load_builtin_demo(self, demo_name: str):
        """Load built-in demo data."""
        try:
            demo_path = Path(self.mimic_directory) / "Mimic/Pi/RecordedData"
            
            if demo_name == "HTV":
                data_folder = demo_path / "HTV"
            elif demo_name == "OFT2":
                data_folder = demo_path / "OFT2"
            elif demo_name == "Disco":
                data_folder = demo_path / "Disco"
            else:
                self._show_error(f"Unknown demo: {demo_name}")
                return
                
            if not data_folder.exists():
                self._show_error(f"Demo folder not found: {data_folder}")
                return
                
            self.current_file = demo_name
            log_info(f"Loaded demo folder: {data_folder}")
            
        except Exception as e:
            log_error(f"Error loading demo: {e}")
            self._show_error(f"Error loading demo: {e}")

    # ---------------------------------------------------------------- Disco Mode
    def start_disco_mode(self):
        """All-in-one disco mode: set data source, speed, and auto-start."""
        try:
            # Set data source to Disco
            self.current_file = "Disco"
            
            # Set playback speed to 1x
            self.playback_speed = 1.0
            
            # Update the speed dropdown to show 1x
            speed_dropdown = getattr(self.ids, 'speed_dropdown', None)
            if speed_dropdown:
                speed_dropdown.text = '1x'
            
            log_info("Disco mode activated: Disco data at 1x speed")
            
            # Update status and check start button
            self._update_status()
            self._check_start_button_state()
            
            # Auto-start the playback
            self.start_playback()
            
        except Exception as e:
            log_error(f"Error starting disco mode: {e}")
            self._show_error(f"Error starting disco mode: {e}")

    # ---------------------------------------------------------------- Speed Control
    def on_dropdown_select_speed(self, speed_str):
        """Set the playback speed multiplier from dropdown text and close it."""
        try:
            # Extract numeric value from "10x", "20x", etc.
            speed_value = float(speed_str.replace('x', ''))
            
            if speed_value <= 0:
                return
                
            self.playback_speed = speed_value
            
            # If currently playing, restart timer with new speed
            if self.is_playing:
                self._stop_playback_timer()
                self._start_playback_timer()
                
            log_info(f"Playback speed set to {speed_value}x")
            
            
            # Update status and check if start button should be enabled
            self._update_status()
            self._check_start_button_state()
            
        except ValueError:
            log_error(f"Invalid speed format: {speed_str}")

    # ---------------------------------------------------------------- Status Updates
    def _update_status(self):
        """Update the status label with current selections and next steps."""
        try:
            status_label = getattr(self.ids, 'status_label', None)
            if not status_label:
                return
                
            if self.is_playing:
                # Show playback status
                status_label.text = f"Playing back {self.current_file} data at {self.playback_speed}x"
                return
                
            if not self.current_file:
                status_label.text = "Select Data to Playback"
                return
                
            if self.playback_speed == 0:
                status_label.text = f"{self.current_file} selected, choose playback speed"
                return
                
            # Both data and speed are selected
            status_label.text = f"{self.current_file} at {self.playback_speed}x - Ready to Start!"
            
        except Exception as e:
            log_error(f"Error updating status: {e}")

    # ---------------------------------------------------------------- Button State Management
    def _update_playback_buttons(self):
        """Update the state of all playback control buttons."""
        try:
            start_button = getattr(self.ids, 'start_button', None)
            stop_button = getattr(self.ids, 'stop_button', None)
            disco_button = getattr(self.ids, 'disco_button', None)
            
            if start_button:
                start_button.disabled = self.is_playing
                
            if stop_button:
                stop_button.disabled = not self.is_playing
                
            if disco_button:
                disco_button.disabled = self.is_playing
                
        except Exception as e:
            log_error(f"Error updating playback buttons: {e}")

    def _check_start_button_state(self):
        """Check if start button should be enabled and update its state."""
        try:
            start_button = getattr(self.ids, 'start_button', None)
            if not start_button:
                return
                
            # Only enable start button if not currently playing AND all conditions are met
            should_enable = (
                not self.is_playing and
                self.current_file and 
                self.playback_speed > 0 and 
                self.arduino_connected
            )
            
            start_button.disabled = not should_enable
            
        except Exception as e:
            log_error(f"Error checking start button state: {e}")

    # ---------------------------------------------------------------- Serial Writing
    def _start_serial_writer(self):
        """Start the serial writer timer to continuously send telemetry data."""
        if self._serial_timer:
            Clock.unschedule(self._serial_timer)
        
        self._serial_timer = Clock.schedule_interval(self._send_telemetry_serial, self._serial_update_interval)
        log_info("Serial writer started")

    def _stop_serial_writer(self):
        """Stop the serial writer timer."""
        if self._serial_timer:
            Clock.unschedule(self._serial_timer)
            self._serial_timer = None
            log_info("Serial writer stopped")

    def _send_telemetry_serial(self, dt):
        """Read telemetry values from database and send to Arduino."""
        if not self.is_playing or not self.arduino_connected:
            return
            
        try:
            # Read current telemetry values from database
            telemetry_values = self._read_current_telemetry()
            
            if telemetry_values:
                # Build the telemetry command string (without LED commands)
                telemetry_cmd = self._build_telemetry_command(telemetry_values)
                
                # Send telemetry data to Arduino
                serialWrite(telemetry_cmd)
                log_info(f"Sent telemetry command: {telemetry_cmd}")
                
                # Build and send LED commands separately
                led_cmd = self._build_led_command(telemetry_values)
                if led_cmd:
                    serialWrite(led_cmd)
                
        except Exception as e:
            log_error(f"Error sending telemetry serial: {e}")

    def _read_current_telemetry(self):
        """Read current telemetry values from the database."""
        try:
            import sqlite3
            
            db_path = self._get_db_path()
            if not db_path:
                return None
                
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Map the Arduino command names to actual database IDs
                telemetry_mapping = {
                    'PSARJ': 'S0000004',      # psarj
                    'SSARJ': 'S0000003',      # ssarj
                    'PTRRJ': 'S0000002',      # ptrrj
                    'STRRJ': 'S0000001',      # strrj
                    'B1B': 'S6000008',        # beta1b
                    'B1A': 'S4000007',        # beta1a
                    'B2B': 'P6000008',        # beta2b
                    'B2A': 'P4000007',        # beta2a
                    'B3B': 'S6000007',        # beta3b
                    'B3A': 'S4000008',        # beta3a
                    'B4B': 'P6000007',        # beta4b
                    'B4A': 'P4000008',        # beta4a
                    'AOS': 'AOS',             # aos
                    'V1A': 'S4000001',        # voltage_1a
                    'V2A': 'P4000001',        # voltage_2a
                    'V3A': 'S4000004',        # voltage_3a
                    'V4A': 'P4000004',        # voltage_4a
                    'V1B': 'S6000004',        # voltage_1b
                    'V2B': 'P6000004',        # voltage_2b
                    'V3B': 'S6000001',        # voltage_3b
                    'V4B': 'P6000001',        # voltage_4b
                    'ISS': 'USLAB000086',     # iss_mode
                    'Sgnt_el': 'Z1000014',    # sgant_elevation
                    'Sgnt_xel': 'Z1000015',   # sgant_xel
                    'Sgnt_xmit': 'Z1000013',  # kuband_transmit
                    'SASA_Xmit': 'S1000009',  # sasa1_status
                    'SASA_AZ': 'S1000004',    # sasa1_azimuth
                    'SASA_EL': 'S1000005'     # sasa1_elevation
                }
                
                # Get the actual database IDs we need to query
                db_ids = list(telemetry_mapping.values())
                
                # Build query to get all values at once
                placeholders = ','.join(['?' for _ in db_ids])
                query = f"SELECT ID, Value FROM telemetry WHERE ID IN ({placeholders})"
                
                cursor.execute(query, db_ids)
                results = cursor.fetchall()
                
                # Convert to dictionary with Arduino command names as keys
                telemetry_dict = {}
                for db_id, value in results:
                    # Find the Arduino command name for this database ID
                    for cmd_name, actual_db_id in telemetry_mapping.items():
                        if actual_db_id == db_id:
                            telemetry_dict[cmd_name] = value
                            break
                
                return telemetry_dict
                
        except Exception as e:
            log_error(f"Error reading telemetry from database: {e}")
            return None

    def _build_telemetry_command(self, telemetry_values):
        """Build the telemetry command string (without LED commands)."""
        try:
            # Extract values with defaults
            psarj = "{:.1f}".format(float(telemetry_values.get('PSARJ', 0)))
            ssarj = "{:.1f}".format(float(telemetry_values.get('SSARJ', 0)))
            ptrrj = "{:.1f}".format(float(telemetry_values.get('PTRRJ', 0)))
            strrj = "{:.1f}".format(float(telemetry_values.get('STRRJ', 0)))
            b1b = "{:.1f}".format(float(telemetry_values.get('B1B', 0)))
            b1a = "{:.1f}".format(float(telemetry_values.get('B1A', 0)))
            b2b = "{:.1f}".format(float(telemetry_values.get('B2B', 0)))
            b2a = "{:.1f}".format(float(telemetry_values.get('B2A', 0)))
            b3b = "{:.1f}".format(float(telemetry_values.get('B3B', 0)))
            b3a = "{:.1f}".format(float(telemetry_values.get('B3A', 0)))
            b4b = "{:.1f}".format(float(telemetry_values.get('B4B', 0)))
            b4a = "{:.1f}".format(float(telemetry_values.get('B4A', 0)))
            aos = telemetry_values.get('AOS', 0)
            module = telemetry_values.get('ISS', 0)
            sgant_elevation = "{:.1f}".format(float(telemetry_values.get('Sgnt_el', 0)))
            sgant_xelevation = "{:.1f}".format(float(telemetry_values.get('Sgnt_xel', 0)))
            sgant_transmit = telemetry_values.get('Sgnt_xmit', 0)
            sasa_xmit = telemetry_values.get('SASA_Xmit', 0)
            sasa_az = "{:.1f}".format(float(telemetry_values.get('SASA_AZ', 0)))
            sasa_el = "{:.1f}".format(float(telemetry_values.get('SASA_EL', 0)))
            
            # Build the telemetry command string (without LED commands)
            telemetry_cmd = (
                f"PSARJ={str(psarj)} "
                f"SSARJ={str(ssarj)} "
                f"PTRRJ={str(ptrrj)} "
                f"STRRJ={str(strrj)} "
                f"B1B={str(b1b)} "
                f"B1A={str(b1a)} "
                f"B2B={str(b2b)} "
                f"B2A={str(b2a)} "
                f"B3B={str(b3b)} "
                f"B3A={str(b3a)} "
                f"B4B={str(b4b)} "
                f"B4A={str(b4a)} "
                f"AOS={str(aos)} "
                f"ISS={str(module)} "
                f"Sgnt_el={str(sgant_elevation)} "
                f"Sgnt_xel={str(sgant_xelevation)} "
                f"Sgnt_xmit={str(sgant_transmit)} "
                f"SASA_Xmit={str(sasa_xmit)} "
                f"SASA_AZ={str(sasa_az)} "
                f"SASA_EL={str(sasa_el)}"
            )
            
            return telemetry_cmd
            
        except Exception as e:
            log_error(f"Error building telemetry command: {e}")
            return ""

    def _build_led_command(self, telemetry_values):
        """Build the LED command string separately."""
        try:
            # Get voltage values for LED control
            v1a = float(telemetry_values.get('V1A', 0))
            v1b = float(telemetry_values.get('V1B', 0))
            v2a = float(telemetry_values.get('V2A', 0))
            v2b = float(telemetry_values.get('V2B', 0))
            v3a = float(telemetry_values.get('V3A', 0))
            v3b = float(telemetry_values.get('V3B', 0))
            v4a = float(telemetry_values.get('V4A', 0))
            v4b = float(telemetry_values.get('V4B', 0))
            
            # Determine LED colors
            if self.current_file == "Disco":
                # Disco mode: random colors
                import random
                led_1a = random.choice(self._disco_colors)
                led_1b = random.choice(self._disco_colors)
                led_2a = random.choice(self._disco_colors)
                led_2b = random.choice(self._disco_colors)
                led_3a = random.choice(self._disco_colors)
                led_3b = random.choice(self._disco_colors)
                led_4a = random.choice(self._disco_colors)
                led_4b = random.choice(self._disco_colors)
            else:
                # Normal mode: voltage-based colors
                led_1a = self._get_voltage_color(v1a)
                led_1b = self._get_voltage_color(v1b)
                led_2a = self._get_voltage_color(v2a)
                led_2b = self._get_voltage_color(v2b)
                led_3a = self._get_voltage_color(v3a)
                led_3b = self._get_voltage_color(v3b)
                led_4a = self._get_voltage_color(v4a)
                led_4b = self._get_voltage_color(v4b)
            
            # Build LED command string
            led_cmd = (
                f"LED_1A={led_1a} "
                f"LED_2A={led_2a} "
                f"LED_3A={led_3a} "
                f"LED_4A={led_4a} "
                f"LED_1B={led_1b} "
                f"LED_2B={led_2b} "
                f"LED_3B={led_3b} "
                f"LED_4B={led_4b}"
            )
            
            log_info(f"LED command: {led_cmd}")
            return led_cmd
            
        except Exception as e:
            log_error(f"Error building LED command: {e}")
            return ""

    def _get_db_path(self):
        """Get the database path based on platform."""
        try:
            import platform
            if platform.system() == "Linux":
                return "/dev/shm/iss_telemetry.db"
            else:
                # Windows path
                import os
                home = os.path.expanduser("~")
                return os.path.join(home, ".mimic_data", "iss_telemetry.db")
        except Exception as e:
            log_error(f"Error getting database path: {e}")
            return None

    def _get_voltage_color(self, voltage):
        """Determine LED color based on voltage threshold."""
        if voltage < 151.5:
            return "Blue"      # Discharging
        elif voltage < 160.0:
            return "Yellow"    # Charging
        else:
            return "White"     # Fully charged

    # ---------------------------------------------------------------- Playback Control
    def start_playback(self):
        """Start playing back the selected data file."""
        if not self.current_file:
            self._show_error("No file selected")
            return
            
        if not self.arduino_connected:
            self._show_error("No Arduino connected")
            return
            
        if self.is_playing:
            self._show_error("Already playing")
            return
            
        try:
            # Determine the data folder path
            if "(USB)" in self.current_file:
                # USB drive file
                drive_name = self.current_file.replace(" (USB)", "")
                data_folder = f"/media/pi/{drive_name}"
            else:
                # Built-in demo
                demo_name = self.current_file
                data_folder = str(Path(self.mimic_directory) / "Mimic/Pi/RecordedData" / demo_name)
            
            # Build command with loop option
            cmd = [
                "python3",
                str(Path(self.mimic_directory) / "Mimic/Pi/RecordedData/playback_engine.py"),
                data_folder,
                str(self.playback_speed)
            ]
            
            # Add loop flag if enabled
            if self.loop_enabled:
                cmd.append("--loop")
            
            # Launch the playback engine
            app = App.get_running_app()
            if hasattr(app, 'playback_proc') and app.playback_proc:
                log_info("Playback already running")
                return
                
            proc = Popen(cmd)
            app.playback_proc = proc
            
            self.is_playing = True
            loop_status = "with looping" if self.loop_enabled else ""
            log_info(f"Started playback of {self.current_file} at {self.playback_speed}x speed {loop_status}")
            
            # Start serial writer
            self._start_serial_writer()
            
            # Update status to show playback is active
            self._update_status()
            
            # Update all button states
            self._update_playback_buttons()
            
        except Exception as e:
            log_error(f"Error starting playback: {e}")
            self._show_error(f"Error starting playback: {e}")

    def stop_playback(self):
        """Stop the current playback."""
        if not self.is_playing:
            return
            
        try:
            log_info("Stopping playback...")
            
            # Stop serial writer first
            self._stop_serial_writer()
            
            # Stop the playback engine
            app = App.get_running_app()
            if hasattr(app, 'playback_proc') and app.playback_proc:
                log_info(f"Terminating process {app.playback_proc.pid}")
                
                # Try graceful termination first
                app.playback_proc.terminate()
                
                # Wait a bit for graceful shutdown
                try:
                    app.playback_proc.wait(timeout=3)
                    log_info("Process terminated gracefully")
                except TimeoutExpired:
                    # Force kill if it doesn't respond
                    log_info("Force killing playback process")
                    app.playback_proc.kill()
                    app.playback_proc.wait()
                    log_info("Process force killed")
                
                app.playback_proc = None
            else:
                log_info("No playback process found to stop")
            
            self.is_playing = False
            log_info("Playback stopped")
            
            # Update status and re-enable all buttons
            self._update_status()
            self._update_playback_buttons()
            
        except Exception as e:
            log_error(f"Error stopping playback: {e}")
            # Even if there's an error, mark as not playing
            self.is_playing = False
            self._stop_serial_writer()
            self._update_status()
            self._update_playback_buttons()
    
    def toggle_loop(self):
        """Toggle loop mode on/off."""
        self.loop_enabled = not self.loop_enabled
        status = "enabled" if self.loop_enabled else "disabled"
        log_info(f"Loop mode {status}")
        
        # Update button appearance
        loop_button = getattr(self.ids, 'loop_button', None)
        if loop_button:
            if self.loop_enabled:
                loop_button.background_color = (0.2, 0.8, 0.2, 1)  # Green
            else:
                loop_button.background_color = (0.6, 0.6, 0.6, 1)  # Gray
            
    # ---------------------------------------------------------------- Error Handling
    def _show_error(self, message: str):
        """Show an error popup."""
        try:
            popup = Popup(
                title='Error',
                content=Label(text=message),
                size_hint=(0.6, 0.3)
            )
            popup.open()
            
            # Auto-close after 3 seconds
            Clock.schedule_once(lambda dt: popup.dismiss(), 3.0)
            
        except Exception as e:
            log_error(f"Error showing error popup: {e}")

    # ---------------------------------------------------------------- Cleanup
    def on_pre_leave(self):
        """Called when leaving the screen."""
        self.stop_playback()
        super().on_pre_leave()
