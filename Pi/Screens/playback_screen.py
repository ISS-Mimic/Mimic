from __future__ import annotations

import pathlib
import time
import threading
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from math import isfinite

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


class _ChangeGate:
    """
    Quantizes angles and only allows a send when something changed
    (or on heartbeat). Greatly reduces bandwidth at 9600 bps.
    """
    def __init__(self, angle_step: float = 0.1, heartbeat_s: float = 1.0):
        self.prev: dict[str, object] = {}
        self.angle_step = angle_step
        self.heartbeat_s = heartbeat_s
        self._last_sent = 0.0

    def _q(self, v):
        try:
            fv = float(v)
            if not isfinite(fv):
                return 0.0
            return round(fv / self.angle_step) * self.angle_step
        except Exception:
            return 0.0

    def filter(self, now: float, vals: dict, leds: dict | None = None):
        """
        Returns (should_send: bool, q_vals: dict, q_leds: dict|None, reason: str)
        reason ∈ {"change", "heartbeat", ""}.
        """
        q_vals = {}
        for k, v in vals.items():
            # Angle-like signals get quantized; flags/ints passed through
            if k.endswith("ARJ") or k.endswith("RRJ") or (k and k[0] == "B"):
                q_vals[k] = self._q(v)
            else:
                q_vals[k] = v

        # Keep LED color strings exactly as computed
        q_leds = {}
        if leds:
            for k, v in leds.items():
                q_leds[k] = "" if v is None else str(v)

        composite = {**q_vals, **q_leds}
        changed = any(self.prev.get(k) != composite[k] for k in composite)
        heartbeat_due = (now - self._last_sent) >= self.heartbeat_s

        if changed or heartbeat_due:
            self.prev = composite
            self._last_sent = now
            reason = "change" if changed else "heartbeat"
            return True, q_vals, (q_leds if leds else None), reason
        return False, q_vals, (q_leds if leds else None), ""

class Playback_Screen(MimicBase):
    """
    Clean, simple playback screen for recorded ISS telemetry data.
    """

    # Playback state
    is_playing = BooleanProperty(False)
    current_file = StringProperty("")
    playback_speed = NumericProperty(0)  # set via dropdown (e.g., 5, 10, 20)

    # Arduino connection status
    arduino_connected = BooleanProperty(False)
    loop_enabled = BooleanProperty(False)

    # Playback data
    _playback_data = []
    _current_index = 0
    _playback_timer = None

    # ======= wire/throughput parameters (NO Arduino changes required) =======
    _BAUD = 9600
    _SAFETY = 0.15         # extra headroom on pacing
    _BASE_HZ = 5           # UI tick target; actual wire pacing enforces 9600
    _ANGLE_STEP = 0.1      # deg
    _HEARTBEAT_S = 5.0     # resend latest state once per 5 seconds (recovery)

    # Serial writing
    _serial_timer = None
    _is_writing_serial = False  # for the Arduino animation
    _gate = None  # initialized in __init__

    # LED control
    _disco_colors = ["Red", "Green", "Blue", "Yellow", "Purple", "Cyan", "White", "Orange"]

    def __init__(self, **kw):
        super().__init__(**kw)
        self._gate = _ChangeGate(angle_step=self._ANGLE_STEP, heartbeat_s=self._HEARTBEAT_S)
        Clock.schedule_interval(self._check_arduino_connection, 5.0)
        self._start_usb_monitor()
        self._update_arduino_animation()

    # ---------------------------------------------------------------- Arduino Check
    def _check_arduino_connection(self, dt):
        """Check if Arduino is connected by checking the arduino count text."""
        try:
            arduino_count_label = getattr(self.ids, 'arduino_count', None)
            if arduino_count_label:
                txt = arduino_count_label.text.strip()
                self.arduino_connected = txt.isdigit() and int(txt) > 0
            else:
                self.arduino_connected = False
        except Exception as e:
            log_error(f"Error checking Arduino connection: {e}")
            self.arduino_connected = False

        self._check_start_button_state()
        if not self.is_playing:
            self._update_arduino_animation()

    # ---------------------------------------------------------------- Arduino Animation
    def _update_arduino_animation(self):
        """Update the Arduino image to show transmit animation when writing serial data, normal when not."""
        try:
            arduino_image = getattr(self.ids, 'arduino', None)
            if not arduino_image:
                return

            if not self.arduino_connected:
                arduino_image.source = f"{self.mimic_directory}/Mimic/Pi/imgs/signal/arduino_offline.png"
            elif self._is_writing_serial:
                arduino_image.source = f"{self.mimic_directory}/Mimic/Pi/imgs/signal/arduino_transmit.zip"
            else:
                arduino_image.source = f"{self.mimic_directory}/Mimic/Pi/imgs/signal/arduino_notransmit.png"
        except Exception as e:
            log_error(f"Error updating Arduino animation: {e}")

    # ---------------------------------------------------------------- USB Monitoring
    def _start_usb_monitor(self):
        """Start background thread to monitor USB drives."""
        def monitor_loop():
            while True:
                try:
                    self._scan_usb_drives()
                    time.sleep(5)
                except Exception as e:
                    log_error(f"USB monitoring error: {e}")
                    time.sleep(10)
        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()

    def _scan_usb_drives(self):
        """Scan for USB drives and update dropdown."""
        try:
            media_dir = Path("/media/pi")
            if not media_dir.exists():
                return
            drives = [d.name for d in media_dir.iterdir() if d.is_dir()]
            Clock.schedule_once(lambda dt: self._update_dropdown(drives))
        except Exception as e:
            log_error(f"USB scan failed: {e}")

    def _update_dropdown(self, drives):
        """Update the file selection dropdown."""
        try:
            dropdown = self.ids.file_dropdown
            if dropdown:
                telemetry_folders = []
                for drive in drives:
                    drive_path = Path(f"/media/pi/{drive}")
                    if drive_path.exists():
                        telemetry_dirs = [d.name for d in drive_path.iterdir()
                                          if d.is_dir() and d.name.startswith("Telemetry_")]
                        for telemetry_dir in telemetry_dirs:
                            display_name = telemetry_dir.replace("Telemetry_", "")
                            telemetry_folders.append(f"USB: {display_name}")

                builtin_demos = ["HTV", "OFT2", "Standard", "Disco"]
                dropdown.values = builtin_demos + telemetry_folders
        except Exception as e:
            log_error(f"Error updating dropdown: {e}")

    # ---------------------------------------------------------------- File Selection
    def on_dropdown_select_data(self, filename):
        """Called when user selects a file from dropdown and close it."""
        if not filename:
            return

        log_info(f"File selected: {filename}")
        if filename.startswith("USB: "):
            display_name = filename.replace("USB: ", "")
            telemetry_folder = f"Telemetry_{display_name}"
            self._load_usb_telemetry_folder(telemetry_folder)
        else:
            self._load_builtin_demo(filename)

        self._update_status()
        self._check_start_button_state()

    def _load_usb_telemetry_folder(self, telemetry_folder: str):
        """Load playback data from USB telemetry folder."""
        try:
            media_dir = Path("/media/pi")
            if not media_dir.exists():
                self._show_error("No USB drives found")
                return

            for drive_dir in media_dir.iterdir():
                if drive_dir.is_dir():
                    telemetry_path = drive_dir / telemetry_folder
                    if telemetry_path.exists() and telemetry_path.is_dir():
                        self.current_file = f"USB: {telemetry_folder}"
                        log_info(f"Loaded USB telemetry folder: {telemetry_path}")
                        return

            self._show_error(f"Telemetry folder '{telemetry_folder}' not found on any USB drive")
        except Exception as e:
            log_error(f"Error loading USB telemetry folder: {e}")
            self._show_error(f"Error loading USB telemetry folder: {e}")

    def _find_usb_telemetry_path(self, telemetry_folder: str) -> Optional[str]:
        """Find the full path to a USB telemetry folder."""
        try:
            media_dir = Path("/media/pi")
            if not media_dir.exists():
                return None
            for drive_dir in media_dir.iterdir():
                if drive_dir.is_dir():
                    telemetry_path = drive_dir / telemetry_folder
                    if telemetry_path.exists() and telemetry_path.is_dir():
                        return str(telemetry_path)
            return None
        except Exception as e:
            log_error(f"Error finding USB telemetry path: {e}")
            return None

    def _load_builtin_demo(self, demo_name: str):
        """Load built-in demo data."""
        try:
            demo_path = Path(self.mimic_directory) / "Mimic/Pi/RecordedData"
            if demo_name == "HTV":
                data_folder = demo_path / "HTV"
            elif demo_name == "OFT2":
                data_folder = demo_path / "OFT2"
            elif demo_name == "Standard":
                data_folder = demo_path / "Standard"
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
            self.current_file = "Disco"
            self.playback_speed = 5.0
            speed_dropdown = getattr(self.ids, 'speed_dropdown', None)
            if speed_dropdown:
                speed_dropdown.text = '5x'
            log_info("Disco mode activated: Disco data at 5x speed")
            self._update_status()
            self._check_start_button_state()
            self.start_playback()
        except Exception as e:
            log_error(f"Error starting disco mode: {e}")
            self._show_error(f"Error starting disco mode: {e}")

    # ---------------------------------------------------------------- Speed Control
    def on_dropdown_select_speed(self, speed_str):
        """Set the playback speed multiplier from dropdown text and close it."""
        try:
            speed_value = float(speed_str.replace('x', ''))
            if speed_value <= 0:
                return
            self.playback_speed = speed_value
            log_info(f"Playback speed set to {speed_value}x")
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
                status_label.text = f"Playing back {self.current_file} data at {self.playback_speed}x"
                return

            if not self.current_file:
                status_label.text = "Select Data to Playback"
                return

            if self.playback_speed == 0:
                status_label.text = f"{self.current_file} selected, choose playback speed"
                return

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
            should_enable = (
                not self.is_playing and
                self.current_file and
                self.playback_speed > 0 and
                self.arduino_connected
            )
            start_button.disabled = not should_enable
        except Exception as e:
            log_error(f"Error checking start button state: {e}")

    # ---------------------------------------------------------------- Serial Writing (Mimic-style)
    def _start_serial_writer(self):
        """Start the serial writer timer to continuously send telemetry data."""
        if self._serial_timer:
            Clock.unschedule(self._serial_timer)
        self._serial_timer = Clock.schedule_once(self._send_telemetry_serial, 0)
        self._is_writing_serial = True
        log_info("Serial writer started with ChangeGate optimization")

    def _stop_serial_writer(self):
        """Stop the serial writer timer."""
        if self._serial_timer:
            Clock.unschedule(self._serial_timer)
            self._serial_timer = None
        self._is_writing_serial = False
        log_info("Serial writer stopped")

    def _send_telemetry_serial(self, dt):
        """Send one combined packet, change-gated and paced for 9600."""
        if not self.is_playing or not self.arduino_connected:
            return

        try:
            vals = self._read_current_telemetry()
            if not vals:
                self._reschedule_serial_writer(1.0 / self._BASE_HZ)
                return

            leds = self._compute_leds(vals)
            now = time.monotonic()
            should_send, q_vals, q_leds, reason = self._gate.filter(now, vals, leds)

            if should_send:
                # Build telemetry command (without LED commands)
                telemetry_cmd = self._build_telemetry_command(q_vals)
                
                # Build LED commands separately
                led_commands = self._build_led_commands(q_vals)

                # If Disco demo, also send a separate DISCO line as requested
                disco_line = "DISCO" if self.current_file == "Disco" else None

                # estimate wire time (include both lines if we’ll send both)
                nb = len((telemetry_cmd + "\n").encode("ascii", "ignore"))
                if disco_line:
                    nb += len((disco_line + "\n").encode("ascii", "ignore"))
                
                # Add LED command bytes to wire time calculation
                for led_cmd in led_commands:
                    nb += len((led_cmd + "\n").encode("ascii", "ignore"))
                
                min_gap = self._min_gap(nb)

                # Send telemetry command first
                self._write_line(telemetry_cmd)
                log_info(f"Playback: sent telemetry ({reason}) → {telemetry_cmd}")
                
                # Small delay to let microcontroller process telemetry command
                time.sleep(0.05)  # 50ms delay
                
                # Send LED commands individually with delays (like mimic screen)
                if led_commands:
                    for led_cmd in led_commands:
                        self._write_line(led_cmd)
                        # Small delay between LED commands
                        time.sleep(0.02)  # 20ms delay
                    log_info(f"Playback: sent {len(led_commands)} LED commands")
                
                # Send DISCO command if needed
                if disco_line:
                    self._write_line(disco_line)
                    log_info(f"Playback: sent DISCO command")

                self._is_writing_serial = True
                self._update_arduino_animation()

                # Calculate total delay time and add to minimum gap
                total_delay = 0.05 + (len(led_commands) * 0.02)  # 50ms + 20ms per LED command
                min_gap = max(min_gap, total_delay)
                
                self._reschedule_serial_writer(max(min_gap, 1.0 / self._BASE_HZ))
            else:
                self._is_writing_serial = False
                self._update_arduino_animation()
                self._reschedule_serial_writer(1.0 / self._BASE_HZ)

        except Exception as e:
            log_error(f"Error sending telemetry serial: {e}")
            self._reschedule_serial_writer(1.0 / self._BASE_HZ)

    def _reschedule_serial_writer(self, interval: float):
        """Reschedule the serial writer with the specified interval."""
        if self._serial_timer:
            Clock.unschedule(self._serial_timer)
        self._serial_timer = Clock.schedule_once(self._send_telemetry_serial, interval)

    # ------------------------------ helpers: writer/pacing/format ------------------------------
    def _write_line(self, line: str):
        """
        Ensure newline termination and call serialWrite once per update.
        """
        if not line.endswith("\n"):
            line = line + "\n"
        try:
            serialWrite(line)
        except Exception as e:
            log_error(f"serialWrite failed: {e}")

    def _line_bytes(self, line: str) -> int:
        return len(line.encode("ascii", "ignore"))

    def _min_gap(self, n_bytes: int) -> float:
        """
        Compute the minimum on-the-wire time for this payload at 9600,
        assuming 10 bits/byte (start + 8 data + stop) plus safety margin.
        """
        bits = n_bytes * 10
        seconds = bits / self._BAUD
        return seconds * (1.0 + self._SAFETY)

    @staticmethod
    def _f(v, places: int = 1) -> str:
        try:
            return f"{float(v):.{places}f}"
        except Exception:
            return f"{0.0:.{places}f}"

    @staticmethod
    def _i(v) -> str:
        try:
            return str(int(round(float(v))))
        except Exception:
            return "0"

    def _compute_leds(self, telemetry_values: dict) -> dict:
        """Voltage → color strings ('Blue'|'Yellow'|'White') for LED_* keys."""
        def color(v):
            v = float(v)
            if v < 151.5:
                return "Blue"
            if v < 160.0:
                return "Yellow"
            return "White"
        leds = {}
        try:
            leds["LED_1A"] = color(telemetry_values.get('V1A', 0))
            leds["LED_1B"] = color(telemetry_values.get('V1B', 0))
            leds["LED_2A"] = color(telemetry_values.get('V2A', 0))
            leds["LED_2B"] = color(telemetry_values.get('V2B', 0))
            leds["LED_3A"] = color(telemetry_values.get('V3A', 0))
            leds["LED_3B"] = color(telemetry_values.get('V3B', 0))
            leds["LED_4A"] = color(telemetry_values.get('V4A', 0))
            leds["LED_4B"] = color(telemetry_values.get('V4B', 0))
        except Exception as e:
            log_error(f"LED compute failed: {e}")
        return leds

    def _build_telemetry_command(self, vals: dict) -> str:
        """Build telemetry command string (without LED commands)."""
        tokens = [
            f"PSARJ={self._f(vals.get('PSARJ'))}",
            f"SSARJ={self._f(vals.get('SSARJ'))}",
            f"PTRRJ={self._f(vals.get('PTRRJ'))}",
            f"STRRJ={self._f(vals.get('STRRJ'))}",
            f"B1B={self._f(vals.get('B1B'))}",
            f"B1A={self._f(vals.get('B1A'))}",
            f"B2B={self._f(vals.get('B2B'))}",
            f"B2A={self._f(vals.get('B2A'))}",
            f"B3B={self._f(vals.get('B3B'))}",
            f"B3A={self._f(vals.get('B3A'))}",
            f"B4B={self._f(vals.get('B4B'))}",
            f"B4A={self._f(vals.get('B4A'))}",
            f"AOS={self._i(vals.get('AOS'))}",
            f"ISS={self._i(vals.get('ISS'))}",
            f"Sgnt_el={self._f(vals.get('Sgnt_el'))}",
            f"Sgnt_xel={self._f(vals.get('Sgnt_xel'))}",
            f"Sgnt_xmit={self._i(vals.get('Sgnt_xmit'))}",
            f"SASA_Xmit={self._i(vals.get('SASA_Xmit'))}",
            f"SASA_AZ={self._f(vals.get('SASA_AZ'))}",
            f"SASA_EL={self._f(vals.get('SASA_EL'))}",
        ]
        return " ".join(tokens)

    def _build_led_commands(self, vals: dict) -> list:
        """Build individual LED commands (like mimic screen)."""
        led_commands = []
        voltage_to_led_mapping = {
            'V1A': '1A', 'V1B': '1B',
            'V2A': '2A', 'V2B': '2B', 
            'V3A': '3A', 'V3B': '3B',
            'V4A': '4A', 'V4B': '4B'
        }
        
        # Build LED commands based on voltage values
        for voltage_key, led_suffix in voltage_to_led_mapping.items():
            if voltage_key in vals:
                try:
                    voltage = float(vals[voltage_key])
                    color = self._get_voltage_color(voltage)
                    led_commands.append(f"LED_{led_suffix}={color}")
                except (ValueError, TypeError):
                    # If voltage conversion fails, default to Blue
                    led_commands.append(f"LED_{led_suffix}=Blue")
        
        return led_commands

    def _get_voltage_color(self, voltage):
        """Determine LED color based on voltage threshold (same as mimic screen)."""
        if voltage < 151.5:
            return "Blue"      # Discharging
        elif voltage < 160.0:
            return "Yellow"    # Charging
        else:
            return "White"     # Fully charged

    # ------------------------------ DB I/O ------------------------------
    def _read_current_telemetry(self):
        """Read current telemetry values from the database."""
        try:
            import sqlite3
            db_path = self._get_db_path()
            if not db_path:
                return None

            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                telemetry_mapping = {
                    'PSARJ': 'S0000004',
                    'SSARJ': 'S0000003',
                    'PTRRJ': 'S0000002',
                    'STRRJ': 'S0000001',
                    'B1B': 'S6000008',
                    'B1A': 'S4000007',
                    'B2B': 'P6000008',
                    'B2A': 'P4000007',
                    'B3B': 'S6000007',
                    'B3A': 'S4000008',
                    'B4B': 'P6000007',
                    'B4A': 'P4000008',
                    'AOS': 'AOS',
                    'V1A': 'S4000001',
                    'V2A': 'P4000001',
                    'V3A': 'S4000004',
                    'V4A': 'P4000004',
                    'V1B': 'S6000004',
                    'V2B': 'P6000004',
                    'V3B': 'S6000001',
                    'V4B': 'P6000001',
                    'ISS': 'USLAB000086',
                    'Sgnt_el': 'Z1000014',
                    'Sgnt_xel': 'Z1000015',
                    'Sgnt_xmit': 'Z1000013',
                    'SASA_Xmit': 'S1000009',
                    'SASA_AZ': 'S1000004',
                    'SASA_EL': 'S1000005'
                }
                db_ids = list(telemetry_mapping.values())
                placeholders = ','.join(['?' for _ in db_ids])
                query = f"SELECT ID, Value FROM telemetry WHERE ID IN ({placeholders})"
                cursor.execute(query, db_ids)
                results = cursor.fetchall()

                telemetry_dict = {}
                for db_id, value in results:
                    for cmd_name, actual_db_id in telemetry_mapping.items():
                        if actual_db_id == db_id:
                            telemetry_dict[cmd_name] = value
                            break

                # Ensure defaults for missing keys to avoid KeyError
                for k in ('PSARJ','SSARJ','PTRRJ','STRRJ',
                          'B1A','B1B','B2A','B2B','B3A','B3B','B4A','B4B',
                          'AOS','ISS','Sgnt_el','Sgnt_xel','Sgnt_xmit','SASA_Xmit','SASA_AZ','SASA_EL',
                          'V1A','V1B','V2A','V2B','V3A','V3B','V4A','V4B'):
                    telemetry_dict.setdefault(k, 0)

                return telemetry_dict
        except Exception as e:
            log_error(f"Error reading telemetry from database: {e}")
            return None

    def _get_db_path(self):
        """Get the database path based on platform."""
        try:
            import platform
            if platform.system() == "Linux":
                return "/dev/shm/iss_telemetry.db"
            else:
                home = os.path.expanduser("~")
                return os.path.join(home, ".mimic_data", "iss_telemetry.db")
        except Exception as e:
            log_error(f"Error getting database path: {e}")
            return None

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
            if self.current_file.startswith("USB: "):
                telemetry_folder = self.current_file.replace("USB: ", "")
                data_folder = self._find_usb_telemetry_path(telemetry_folder)
                if not data_folder:
                    self._show_error(f"Could not find USB telemetry folder: {telemetry_folder}")
                    return
            else:
                demo_name = self.current_file
                data_folder = str(Path(self.mimic_directory) / "Mimic/Pi/RecordedData" / demo_name)

            cmd = [
                "python3",
                str(Path(self.mimic_directory) / "Mimic/Pi/RecordedData/playback_engine.py"),
                data_folder,
                str(self.playback_speed)
            ]
            if self.loop_enabled:
                cmd.append("--loop")

            app = App.get_running_app()
            env = os.environ.copy()
            env.pop('PYTHONPATH', None)
            env.pop('PYTHONHOME', None)

            proc = Popen(cmd, env=env)
            app.playback_proc = proc

            self.is_playing = True
            loop_status = "with looping" if self.loop_enabled else ""
            log_info(f"Started playback of {self.current_file} at {self.playback_speed}x speed {loop_status}")

            self._start_serial_writer()
            self._update_status()
            self._update_playback_buttons()
            self._update_arduino_animation()

        except Exception as e:
            log_error(f"Error starting playback: {e}")
            import traceback
            log_error(f"Traceback: {traceback.format_exc()}")
            self._show_error(f"Error starting playback: {e}")

    def stop_playback(self):
        """Stop the current playback."""
        if not self.is_playing:
            return
        try:
            log_info("Stopping playback...")

            self._stop_serial_writer()

            app = App.get_running_app()
            if hasattr(app, 'playback_proc') and app.playback_proc:
                log_info(f"Terminating process {app.playback_proc.pid}")

                # Only send RESET if we’re actually playing and have a process
                serialWrite("RESET")

                app.playback_proc.terminate()
                try:
                    app.playback_proc.wait(timeout=3)
                    log_info("Process terminated gracefully")
                except TimeoutExpired:
                    log_info("Force killing playback process")
                    app.playback_proc.kill()
                    app.playback_proc.wait()
                    log_info("Process force killed")
                app.playback_proc = None
            else:
                log_info("No playback process found to stop")

            self.is_playing = False
            log_info("Playback stopped")

            self._update_status()
            self._update_playback_buttons()
            self._update_arduino_animation()

        except Exception as e:
            log_error(f"Error stopping playback: {e}")
            self.is_playing = False
            self._stop_serial_writer()
            self._update_status()
            self._update_playback_buttons()
            self._update_arduino_animation()

    def toggle_loop(self):
        """Toggle loop mode on/off."""
        self.loop_enabled = not self.loop_enabled
        status = "enabled" if self.loop_enabled else "disabled"
        log_info(f"Loop mode {status}")
        loop_button = getattr(self.ids, 'loop_button', None)
        if loop_button:
            loop_button.background_color = (0.2, 0.8, 0.2, 1) if self.loop_enabled else (0.6, 0.6, 0.6, 1)

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
            Clock.schedule_once(lambda dt: popup.dismiss(), 3.0)
        except Exception as e:
            log_error(f"Error showing error popup: {e}")

    # ---------------------------------------------------------------- Cleanup
    def on_pre_leave(self):
        """Called when leaving the screen."""
        self.stop_playback()
        self._update_arduino_animation()
        super().on_pre_leave()
