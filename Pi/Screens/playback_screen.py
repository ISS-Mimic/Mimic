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
                builtin_demos = ["HTV", "OFT2", "Disco"]
                
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
                
            if not self.current_file:
                status_label.text = "Select Data to Playback"
                return
                
            if self.playback_speed == 0:  # Changed from "not self.playback_speed"
                status_label.text = f"{self.current_file} selected, choose playback speed"
                return
                
            # Both data and speed are selected
            status_label.text = f"{self.current_file} at {self.playback_speed}x - Ready to Start!"
            
        except Exception as e:
            log_error(f"Error updating status: {e}")

    def _check_start_button_state(self):
        """Check if start button should be enabled and update its state."""
        try:
            start_button = getattr(self.ids, 'start_button', None)
            if not start_button:
                return
                
            # Enable start button if all conditions are met
            should_enable = (
                self.current_file and 
                self.playback_speed > 0 and  # Changed from "self.playback_speed"
                self.arduino_connected
            )
            
            start_button.disabled = not should_enable
            
        except Exception as e:
            log_error(f"Error checking start button state: {e}")

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
            
        except Exception as e:
            log_error(f"Error starting playback: {e}")
            self._show_error(f"Error starting playback: {e}")

    def stop_playback(self):
        """Stop the current playback."""
        if not self.is_playing:
            return
            
        try:
            # Stop the playback engine
            app = App.get_running_app()
            if hasattr(app, 'playback_proc') and app.playback_proc:
                # Try graceful termination first
                app.playback_proc.terminate()
                
                # Wait a bit for graceful shutdown
                try:
                    app.playback_proc.wait(timeout=3)
                except TimeoutExpired:
                    # Force kill if it doesn't respond
                    log_info("Force killing playback process")
                    app.playback_proc.kill()
                    app.playback_proc.wait()
                
                app.playback_proc = None
            
            self.is_playing = False
            log_info("Playback stopped")
            
        except Exception as e:
            log_error(f"Error stopping playback: {e}")
    
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
