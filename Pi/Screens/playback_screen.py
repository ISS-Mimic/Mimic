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
    playback_speed = NumericProperty(1.0)  # 1.0 = real-time, 2.0 = 2x speed, etc.
    
    # Arduino connection status
    arduino_connected = BooleanProperty(False)
    
    # Playback data
    _playback_data = []
    _current_index = 0
    _playback_timer = None

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
                    print(f"Arduino count from label: {arduino_count}")
                else:
                    self.arduino_connected = False
                    print("Arduino count label is empty or not a number")
            else:
                self.arduino_connected = False
                print("No arduino_count label found")
                
        except Exception as e:
            log_error(f"Error checking Arduino connection: {e}")
            self.arduino_connected = False

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
                builtin_demos = ["HTV Demo", "OFT-2 Demo", "Standard Demo"]
                
                dropdown.values = usb_files + builtin_demos
                
        except Exception as e:
            log_error(f"Error updating dropdown: {e}")

    # ---------------------------------------------------------------- File Selection
    def on_file_selected(self, filename: str):
        """Called when user selects a file from dropdown."""
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

    def _load_usb_file(self, drive_name: str):
        """Load playback data from USB drive."""
        try:
            # Look for common data file formats
            usb_path = Path(f"/media/pi/{drive_name}")
            
            # Find data files (you can customize this based on your format)
            data_files = list(usb_path.glob("*.csv")) + list(usb_path.glob("*.json"))
            
            if not data_files:
                self._show_error("No data files found on USB drive")
                return
                
            # For now, just show the first file found
            # Later we can add file selection
            self._load_data_file(data_files[0])
            
        except Exception as e:
            log_error(f"Error loading USB file: {e}")
            self._show_error(f"Error loading USB file: {e}")

    def _load_builtin_demo(self, demo_name: str):
        """Load built-in demo data."""
        try:
            demo_path = Path(self.mimic_directory) / "Mimic/Pi/RecordedData"
            
            if demo_name == "HTV Demo":
                data_file = demo_path / "htv_data.csv"  # or whatever format you use
            elif demo_name == "OFT-2 Demo":
                data_file = demo_path / "oft2_data.csv"
            elif demo_name == "Standard Demo":
                data_file = demo_path / "standard_data.csv"
            else:
                self._show_error(f"Unknown demo: {demo_name}")
                return
                
            if not data_file.exists():
                self._show_error(f"Demo file not found: {data_file}")
                return
                
            self._load_data_file(data_file)
            
        except Exception as e:
            log_error(f"Error loading demo: {e}")
            self._show_error(f"Error loading demo: {e}")

    def _load_data_file(self, file_path: Path):
        """Load and parse the actual data file."""
        try:
            # This is where you'd implement your data loading logic
            # For now, just set the filename
            self.current_file = file_path.name
            log_info(f"Loaded data file: {file_path}")
            
            # TODO: Parse the actual data file and store in self._playback_data
            # This will depend on your data format (CSV, JSON, etc.)
            
        except Exception as e:
            log_error(f"Error loading data file: {e}")
            self._show_error(f"Error loading data file: {e}")

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
            # TODO: Start the actual playback
            # This will involve:
            # 1. Reading the data file
            # 2. Setting up a timer to send data at the right intervals
            # 3. Sending data to Arduino via serialWrite
            
            self.is_playing = True
            log_info(f"Started playback of {self.current_file}")
            
            # For now, just simulate playback
            self._start_playback_timer()
            
        except Exception as e:
            log_error(f"Error starting playback: {e}")
            self._show_error(f"Error starting playback: {e}")

    def stop_playback(self):
        """Stop the current playback."""
        if not self.is_playing:
            return
            
        try:
            self._stop_playback_timer()
            self.is_playing = False
            log_info("Playback stopped")
            
        except Exception as e:
            log_error(f"Error stopping playback: {e}")

    def _start_playback_timer(self):
        """Start the timer for sending playback data."""
        # Calculate interval based on playback speed
        # If original data was sent every 100ms and speed is 2x, send every 50ms
        base_interval = 0.1  # 100ms base interval
        interval = base_interval / self.playback_speed
        
        self._playback_timer = Clock.schedule_interval(self._send_playback_data, interval)

    def _stop_playback_timer(self):
        """Stop the playback timer."""
        if self._playback_timer:
            self._playback_timer.cancel()
            self._playback_timer = None

    def _send_playback_data(self, dt):
        """Send the next piece of playback data to Arduino."""
        try:
            # TODO: Get the next data point from self._playback_data
            # For now, just send a placeholder
            if self.arduino_connected:
                serialWrite("PLAYBACK_DATA")
                
        except Exception as e:
            log_error(f"Error sending playback data: {e}")

    # ---------------------------------------------------------------- Speed Control
    def set_playback_speed(self, speed: float):
        """Set the playback speed multiplier."""
        if speed <= 0:
            return
            
        self.playback_speed = speed
        
        # If currently playing, restart timer with new speed
        if self.is_playing:
            self._stop_playback_timer()
            self._start_playback_timer()
            
        log_info(f"Playback speed set to {speed}x")

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
