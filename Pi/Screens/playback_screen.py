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
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.checkbox import CheckBox

from kivy.core.window import Window
from kivy.graphics import Color, Rectangle

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

    name = StringProperty("playback")

    # File and UI state
    file_source = StringProperty("")
    file_path = StringProperty("")
    dropdown_visible = BooleanProperty(False)

    # Playback status
    is_playing = BooleanProperty(False)
    loop_playback = BooleanProperty(False)
    speed = NumericProperty(1.0)

    # UI Controls
    _dropdown_popup: Optional[Popup] = None
    _dropdown_spinner: Optional[Spinner] = None

    # Serial writing
    _serial_timer = None
    _serial_update_interval = 0.1  # Update every 100ms (10Hz)

    # Timestamp of last successful serial send (monotonic seconds)
    _last_serial_send_ts: float = 0.0

    # LED control
    _disco_colors = ["Red", "Green", "Blue", "Yellow", "Purple", "Cyan", "White", "Orange"]

    # Local process management
    _local_playback_proc = None

    def _set_local_playback_proc(self, value):
        """Setter for _local_playback_proc to track changes."""
        old_value = self._local_playback_proc
        print(f"DEBUG: _local_playback_proc changing from {old_value} to {value}")
        if old_value and value is None:
            print("DEBUG: WARNING: _local_playback_proc being set to None!")
        self._local_playback_proc = value

    # ---------------------------------------------------------------- Lifecycle
    def on_pre_enter(self):
        super().on_pre_enter()
        Clock.schedule_once(lambda dt: self._update_status(), 0)
        Clock.schedule_once(lambda dt: self._update_playback_buttons(), 0)
        Clock.schedule_once(lambda dt: self._update_arduino_animation(), 0)

    def on_pre_leave(self):
        """Leaving the screen should NOT auto-stop playback; just refresh icon."""
        log_info("Playback_Screen.on_pre_leave() — not auto-stopping.")
        self._update_arduino_animation()
        super().on_pre_leave()

    # ---------------------------------------------------------------- UI Helpers
    def _update_status(self):
        try:
            status_label = getattr(self.ids, 'status', None)
            if status_label:
                if self.is_playing:
                    status_label.text = f"Playing at {self.speed}x"
                else:
                    status_label.text = "Stopped"
        except Exception as e:
            log_error(f"Error updating status: {e}")

    def _update_playback_buttons(self):
        try:
            play_btn = getattr(self.ids, 'play_btn', None)
            stop_btn = getattr(self.ids, 'stop_btn', None)
            loop_chk = getattr(self.ids, 'loop_chk', None)

            if play_btn:
                play_btn.disabled = self.is_playing is True
            if stop_btn:
                stop_btn.disabled = self.is_playing is False
            if loop_chk:
                loop_chk.active = self.loop_playback
        except Exception as e:
            log_error(f"Error updating buttons: {e}")

    def _update_usb_label(self):
        try:
            usb_label = getattr(self.ids, 'usb_label', None)
            if usb_label:
                usb_label.text = self.file_source or ""
        except Exception as e:
            log_error(f"Error updating usb label: {e}")

    # ---------------------------------------------------------------- Process status
    def _check_playback_process_status(self):
        """Check if the playback process is still running and update is_playing accordingly."""
        try:
            print("DEBUG: _check_playback_process_status called")
            print(f"DEBUG: local_playback_proc: {self._local_playback_proc}")

            if self._local_playback_proc:
                print(f"DEBUG: local_playback_proc exists: {self._local_playback_proc}")
                print(f"DEBUG: local_playback_proc pid: {self._local_playback_proc.pid}")

                # Check if process is still alive
                poll_result = self._local_playback_proc.poll()
                print(f"DEBUG: poll() result: {poll_result}")

                if poll_result is None:
                    # Process is still running
                    if not self.is_playing:
                        print("DEBUG: Process running and is_playing was False - fixing")
                        self.is_playing = True
                        self._update_status()
                        self._update_playback_buttons()
                    else:
                        print("DEBUG: Process running and is_playing is already True")
                else:
                    # Process has ended
                    print(f"DEBUG: Process has ended with return code: {poll_result}")
                    print(f"DEBUG: Process args: {self._local_playback_proc.args}")

                    # Only consider it truly ended if return code is 0 (normal exit)
                    # Negative values indicate signals (like SIGTERM) which might be premature
                    if poll_result == 0:
                        print("DEBUG: Process ended normally (return code 0)")
                        if self.is_playing:
                            print("DEBUG: Playback process ended normally - stopping playback")
                            self.is_playing = False
                            self._set_local_playback_proc(None)
                            self._update_status()
                            self._update_playback_buttons()
                    else:
                        print(f"DEBUG: Process terminated by signal (return code {poll_result}) - keeping reference")
                        # Don't clear the process reference for signal termination
                        # The process might still be running or might restart
                        pass
            else:
                # No local playback process
                print("DEBUG: No local_playback_proc found")
                if self.is_playing:
                    print("DEBUG: No playback process but is_playing was True - fixing")
                    self.is_playing = False
                else:
                    print("DEBUG: No playback process and is_playing is already False")

        except Exception as e:
            log_error(f"Error checking playback process status: {e}")

    # ---------------------------------------------------------------- Arduino icon (Option B)
    def _update_arduino_animation(self):
        """Pure UI update: choose icon based on connection and recent serial activity, not process state."""
        try:
            print(f"DEBUG: _update_arduino_animation called")
            print(f"DEBUG: arduino_connected = {self.arduino_connected}")
            print(f"DEBUG: is_playing = {self.is_playing}")
            print(f"DEBUG: mimic_directory = {self.mimic_directory}")

            arduino_image = getattr(self.ids, 'arduino', None)
            if not arduino_image:
                print("DEBUG: arduino image not found in ids")
                return
            else:
                print(f"DEBUG: arduino image found: {arduino_image}")

            # Consider it "transmitting" if we pushed bytes in the last 0.5 s
            try:
                recently_sent = (time.monotonic() - getattr(self, "_last_serial_send_ts", 0.0)) < 0.5
            except Exception:
                recently_sent = False

            if not self.arduino_connected:
                target_source = f"{self.mimic_directory}/Mimic/Pi/imgs/signal/arduino_offline.png"
                target_state = "offline"
            elif recently_sent:
                target_source = f"{self.mimic_directory}/Mimic/Pi/imgs/signal/Arduino_Transmit.zip"
                target_state = "transmit"
            else:
                target_source = f"{self.mimic_directory}/Mimic/Pi/imgs/signal/arduino_notransmit.png"
                target_state = "normal"

            # Only update if the source is different (avoid unnecessary changes)
            if arduino_image.source != target_source:
                print(f"DEBUG: Changing arduino image from {arduino_image.source} to {target_source}")
                print(f"DEBUG: State: {target_state}")
                arduino_image.source = target_source
            else:
                print(f"DEBUG: Arduino image already correct: {target_state}")

        except Exception as e:
            log_error(f"Error updating Arduino animation: {e}")

    # ---------------------------------------------------------------- File Selection
    def on_dropdown_open(self):
        try:
            if self._dropdown_popup:
                self._dropdown_popup.dismiss()
                self._dropdown_popup = None

            layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
            spinner = Spinner(text='Select source', values=('USB', 'SD Card', 'DB in RAM (/dev/shm)'), size_hint=(1, None), height=44)
            layout.add_widget(spinner)
            btn_close = Button(text='Close', size_hint=(1, None), height=44)
            btn_close.bind(on_release=lambda *a: self._dropdown_popup.dismiss())
            layout.add_widget(btn_close)

            popup = Popup(title='Select Data Source', content=layout, size_hint=(0.8, 0.6))
            self._dropdown_popup = popup
            self._dropdown_spinner = spinner
            popup.open()
        except Exception as e:
            log_error(f"Error opening dropdown: {e}")

    def on_dropdown_dismiss(self):
        try:
            if self._dropdown_popup:
                self._dropdown_popup.dismiss()
                self._dropdown_popup = None
        except Exception as e:
            log_error(f"Error dismissing dropdown: {e}")

    def on_dropdown_select(self, source):
        try:
            self.file_source = source
            self._update_usb_label()
            self._populate_file_list(source)
        except Exception as e:
            log_error(f"Error updating dropdown: {e}")

    # ---------------------------------------------------------------- File Selection
    def on_dropdown_select_data(self, filename):
        """Called when user selects a file from dropdown and close it."""
        if not filename:
            return

        log_info(f"File selected: {filename}")

        # Parse the selection
        if filename.startswith("USB: "):
            # Example path translation
            rel = filename.replace("USB: ", "").strip()
            self.file_path = f"/media/usb/{rel}"
            self.file_source = "USB"
        elif filename.startswith("SD: "):
            rel = filename.replace("SD: ", "").strip()
            self.file_path = f"/home/pi/RecordedData/{rel}"
            self.file_source = "SD"
        elif filename.startswith("DB: "):
            self.file_source = "/dev/shm"
            self.file_path = ""
        else:
            # Raw path
            self.file_path = filename
            self.file_source = ""

        self._update_usb_label()

    # ---------------------------------------------------------------- Populate files
    def _populate_file_list(self, source: str):
        try:
            dropdown = getattr(self.ids, 'file_list', None)
            if not dropdown:
                return

            files = []
            if source == 'USB':
                base = Path('/media/usb')
                files = [f"USB: {p.name}" for p in base.glob('*.csv')]
            elif source == 'SD Card':
                base = Path('/home/pi/RecordedData')
                files = [f"SD: {p.name}" for p in base.glob('*.csv')]
            elif source.startswith('DB'):
                files = ["DB: /dev/shm/iss_telemetry.db"]

            dropdown.values = files
        except Exception as e:
            log_error(f"Error populating file list: {e}")

    # ---------------------------------------------------------------- Start/Stop playback
    def start_playback(self):
        """Start playback using the selected source."""
        try:
            if self.is_playing:
                log_info("Playback already running")
                return

            # Validate source
            if self.file_source.startswith('DB'):
                db_path = '/dev/shm/iss_telemetry.db'
                if not Path(db_path).exists():
                    log_error("DB in RAM not found: /dev/shm/iss_telemetry.db")
                    return
                self._start_db_playback(db_path)
            else:
                if not self.file_path:
                    log_error("No file selected for playback")
                    return
                self._start_file_playback(self.file_path)

            # Mark state and update UI
            self.is_playing = True
            self._update_status()
            self._update_playback_buttons()
            self._update_arduino_animation()

            # Start serial writer (sends current telemetry to Arduino)
            self._start_serial_writer()

        except Exception as e:
            log_error(f"Error starting playback: {e}")

    def stop_playback(self):
        """Stop the current playback."""
        if not self.is_playing:
            return
        try:
            log_info("Stopping playback...")
            self._stop_serial_writer()

            # Terminate any local process
            if self._local_playback_proc:
                log_info(f"Terminating process {self._local_playback_proc.pid}")
                try:
                    serialWrite("RESET")
                except Exception:
                    pass

                try:
                    self._local_playback_proc.terminate()
                    self._local_playback_proc.wait(timeout=3)
                    log_info("Process terminated gracefully")
                except TimeoutExpired:
                    log_info("Force killing playback process")
                    self._local_playback_proc.kill()
                    self._local_playback_proc.wait()
                    log_info("Process force killed")

                self._set_local_playback_proc(None)

            self.is_playing = False
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

    # ---------------------------------------------------------------- Launch engine
    def _start_file_playback(self, csv_path: str):
        try:
            mimic_dir = self.mimic_directory or str(Path.home())
            engine = Path(mimic_dir) / 'Mimic' / 'Pi' / 'RecordedData' / 'playback_engine.py'

            if not engine.exists():
                log_error(f"Playback engine not found: {engine}")
                return

            speed = float(self.speed or 1.0)
            loop_flag = '--loop' if self.loop_playback else ''

            args = ['python3', str(engine), '--csv', csv_path, '--speed', str(speed)]
            if loop_flag:
                args.append(loop_flag)

            proc = Popen(args)
            self._set_local_playback_proc(proc)
            log_info(f"Started playback engine for file: {csv_path}")
        except Exception as e:
            log_error(f"Error starting file playback: {e}")

    def _start_db_playback(self, db_path: str):
        try:
            mimic_dir = self.mimic_directory or str(Path.home())
            engine = Path(mimic_dir) / 'Mimic' / 'Pi' / 'RecordedData' / 'playback_engine.py'

            if not engine.exists():
                log_error(f"Playback engine not found: {engine}")
                return

            speed = float(self.speed or 1.0)
            loop_flag = '--loop' if self.loop_playback else ''

            args = ['python3', str(engine), '--db', db_path, '--speed', str(speed)]
            if loop_flag:
                args.append(loop_flag)

            proc = Popen(args)
            self._set_local_playback_proc(proc)
            log_info(f"Started playback from DB: {db_path}")
        except Exception as e:
            log_error(f"Error starting DB playback: {e}")

    # ---------------------------------------------------------------- Serial I/O
    def _start_serial_writer(self):
        """Schedule periodic serial writes to Arduino while playing."""
        try:
            if self._serial_timer:
                Clock.unschedule(self._serial_timer)

            self._serial_timer = Clock.schedule_interval(self._send_telemetry_serial, self._serial_update_interval)
            log_info("Serial writer started")
        except Exception as e:
            log_error(f"Error starting serial writer: {e}")

    def _stop_serial_writer(self):
        """Unschedule serial writes."""
        try:
            if self._serial_timer:
                Clock.unschedule(self._serial_timer)
                self._serial_timer = None
                log_info("Serial writer stopped")
        except Exception as e:
            log_error(f"Error stopping serial writer: {e}")

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

                # Mark recent serial activity and refresh Arduino animation
                try:
                    self._last_serial_send_ts = time.monotonic()
                except Exception:
                    # time.monotonic() should always exist, but guard just in case
                    self._last_serial_send_ts = 0.0
                self._update_arduino_animation()

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
                    'SSARJ': 'S0000005',      # ssarj
                    'S4SAW': 'S0000006',      # s4_saw_alpha
                    'P4SAW': 'S0000007',      # p4_saw_alpha
                    'S6SAW': 'S0000008',      # s6_saw_alpha
                    'P6SAW': 'S0000009',      # p6_saw_alpha
                    'STRAL': 'S0000010',      # sarj_rate
                    'PSTRL': 'S0000011',      # psarj_rate
                    'SSTRL': 'S0000012',      # ssarj_rate
                    'BETA':  'S0000013',      # beta_angle
                }

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
            log_error(f"Error reading current telemetry: {e}")
            return None

    def _build_telemetry_command(self, values: Dict[str, Any]) -> str:
        """Build the telemetry command string for Arduino (without LEDs)."""
        # Example: CMD:PSARJ=123.45;SSARJ=234.56;...
        try:
            parts = []
            for key in ('PSARJ', 'SSARJ', 'S4SAW', 'P4SAW', 'S6SAW', 'P6SAW', 'STRAL', 'PSTRL', 'SSTRL', 'BETA'):
                if key in values:
                    parts.append(f"{key}={values[key]}")
            return "CMD:" + ";".join(parts)
        except Exception as e:
            log_error(f"Error building telemetry command: {e}")
            return "CMD:"

    def _build_led_command(self, values: Dict[str, Any]) -> Optional[str]:
        """Build optional LED command based on telemetry (or None)."""
        try:
            # Simple example: blink a color based on BETA value
            beta = values.get('BETA', 0)
            if beta is None:
                return None

            try:
                beta = float(beta)
            except Exception:
                return None

            if beta > 30:
                color = "Red"
            elif beta > 10:
                color = "Yellow"
            else:
                color = "Blue"

            return f"LED:{color}"
        except Exception as e:
            log_error(f"Error building LED command: {e}")
            return None

    # ---------------------------------------------------------------- Paths / helpers
    def _get_db_path(self) -> Optional[str]:
        try:
            if self.file_source.startswith('DB'):
                return '/dev/shm/iss_telemetry.db'
            return None
        except Exception:
            return None

    # ---------------------------------------------------------------- Misc UI
    def on_speed_change(self, value):
        try:
            self.speed = float(value)
            self._update_status()
        except Exception as e:
            log_error(f"Error changing speed: {e}")

    def on_loop_toggle(self, active):
        try:
            self.loop_playback = bool(active)
        except Exception as e:
            log_error(f"Error toggling loop: {e}")

    def on_arduino_toggle(self, active):
        try:
            self.arduino_connected = bool(active)
            self._update_arduino_animation()
        except Exception as e:
            log_error(f"Error toggling Arduino: {e}")

    # ---------------------------------------------------------------- Debug helpers
    def debug_force_transmit(self):
        """Debug button to force transmit icon for 1 second."""
        try:
            self._last_serial_send_ts = time.monotonic()
            self._update_arduino_animation()
        except Exception:
            pass
