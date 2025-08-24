from __future__ import annotations

from pathlib import Path
import pathlib
import subprocess
from subprocess import Popen
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty
from kivy.lang import Builder
from kivy.app import App
import sqlite3
import time
from kivy.clock import Clock

from ._base import MimicBase                    # gives mimic_directory + signalcolor
from utils.logger import log_info, log_error
from utils.serial import serialWrite

# -- load KV that sits next to this file -------------------------------------
kv_path = pathlib.Path(__file__).with_name("MimicScreen.kv")
Builder.load_file(str(kv_path))

class MimicScreen(MimicBase):
    log_info("MimicScreen loaded")
    """
    Live ISS telemetry hub.
    Starts / stops iss_telemetry.py and TDRScheck.py, toggled by a
    'Mimic' button in the GUI.
    Now includes direct serialWrite functionality for LED control.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._mimic_active = False
        self._mimic_event = None
        self._current_telemetry_index = 0
        self._telemetry_data = []
        self._db_path = None

    # ------------------------------------------------------------------- UI
    def mimic_transmit(self, value: bool) -> None:
        """
        Bound in KV.  True ? transmit; False ? idle.
        Now directly controls mimic telemetry instead of just setting a boolean.
        """
        if value:
            self.start_mimic_telemetry()
        else:
            self.stop_mimic_telemetry()
        log_info(f"Start Mimic Telemetry: {value}")
    
    def start_mimic_telemetry(self):
        """Start mimic telemetry transmission."""
        try:
            if self._mimic_active:
                log_info("Mimic telemetry already active")
                return
                
            # Load telemetry data from database
            self._load_telemetry_data()
            
            if not self._telemetry_data:
                log_error("No telemetry data found in database")
                return
            
            # Start telemetry transmission
            self._mimic_active = True
            self._current_telemetry_index = 0
            
            # Schedule telemetry updates every 100ms (10x speed)
            self._mimic_event = Clock.schedule_interval(self._send_mimic_telemetry, 0.1)
            
            log_info("Mimic telemetry started")
            
        except Exception as exc:
            log_error(f"Failed to start mimic telemetry: {exc}")
    
    def stop_mimic_telemetry(self):
        """Stop mimic telemetry transmission."""
        try:
            if not self._mimic_active:
                return
                
            self._mimic_active = False
            
            if self._mimic_event:
                self._mimic_event.cancel()
                self._mimic_event = None
            
            # Send RESET command to stop all LEDs
            serialWrite("RESET")
            log_info("Mimic telemetry stopped")
            
        except Exception as exc:
            log_error(f"Failed to stop mimic telemetry: {exc}")
    
    def _load_telemetry_data(self):
        """Load telemetry data from database."""
        try:
            # Use the same database path as other screens
            self._db_path = "/dev/shm/iss_telemetry.db"
            
            if not Path(self._db_path).exists():
                log_error(f"Telemetry database not found: {self._db_path}")
                return
            
            # Connect to database and load telemetry data
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            # Use the same telemetry mapping as playback screen
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
            
            log_info(f"Mimic Screen: Querying database with IDs: {db_ids}")
            
            cursor.execute(query, db_ids)
            results = cursor.fetchall()
            
            if results:
                # Convert to dictionary with Arduino command names as keys
                telemetry_dict = {}
                for db_id, value in results:
                    # Find the Arduino command name for this database ID
                    for cmd_name, actual_db_id in telemetry_mapping.items():
                        if actual_db_id == db_id:
                            telemetry_dict[cmd_name] = value
                            break
                
                log_info(f"Mimic Screen: Loaded telemetry data: {telemetry_dict}")
                
                # Debug: Check for missing values
                missing_values = []
                for cmd_name in telemetry_mapping.keys():
                    if cmd_name not in telemetry_dict:
                        missing_values.append(cmd_name)
                
                if missing_values:
                    log_info(f"Mimic Screen: Missing values: {missing_values}")
                
                # Store the telemetry data for use in sending
                self._telemetry_data = [telemetry_dict]  # Single record for now
                log_info(f"Loaded {len(self._telemetry_data)} telemetry records")
            else:
                log_error("No telemetry records found in database")
            
            conn.close()
            
        except Exception as exc:
            log_error(f"Failed to load telemetry data: {exc}")
    
    def _send_mimic_telemetry(self, dt):
        """Send telemetry data over serial."""
        try:
            if not self._mimic_active or not self._telemetry_data:
                return
            
            # Get current telemetry record
            record = self._telemetry_data[self._current_telemetry_index]
            
            # Debug: Print the current record
            log_info(f"Mimic Screen: Record {self._current_telemetry_index}: {record}")
            
            # Build telemetry command (same format as playback screen)
            telemetry_cmd = self._build_telemetry_command(record)
            
            # Debug: Print the telemetry command
            log_info(f"Mimic Screen: Sending telemetry: {telemetry_cmd}")
            
            # Send telemetry command
            serialWrite(telemetry_cmd)
            
            # Small delay to let microcontroller process telemetry command (same as playback screen)
            time.sleep(0.05)  # 50ms delay
            
            # Send LED commands (same logic as playback screen)
            self._send_led_commands(record)
            
            # Move to next record (loop back to start)
            self._current_telemetry_index = (self._current_telemetry_index + 1) % len(self._telemetry_data)
            
        except Exception as exc:
            log_error(f"Failed to send mimic telemetry: {exc}")
    
    def _build_telemetry_command(self, telemetry_values):
        """Build the telemetry command string (same as playback screen)."""
        try:
            # Extract values with defaults (same as playback screen)
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
            sgant_elevation = "{:.1f}".format(float(telemetry_values.get('Sgnt_el', 0)))
            sgant_xelevation = "{:.1f}".format(float(telemetry_values.get('Sgnt_xel', 0)))
            sgant_transmit = telemetry_values.get('Sgnt_xmit', 0)
            sasa_xmit = telemetry_values.get('SASA_Xmit', 0)
            sasa_az = "{:.1f}".format(float(telemetry_values.get('SASA_AZ', 0)))
            sasa_el = "{:.1f}".format(float(telemetry_values.get('SASA_EL', 0)))
            
            # Build the telemetry command string (same as playback screen)
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
    
    def _send_led_commands(self, record):
        """Send LED commands based on telemetry data."""
        try:
            # Debug: Print voltage values
            log_info(f"Mimic Screen: Voltage values - V1A: {record.get('V1A', 'N/A')}, V1B: {record.get('V1B', 'N/A')}, V2A: {record.get('V2A', 'N/A')}, V2B: {record.get('V2B', 'N/A')}, V3A: {record.get('V3A', 'N/A')}, V3B: {record.get('V3B', 'N/A')}, V4A: {record.get('V4A', 'N/A')}, V4B: {record.get('V4B', 'N/A')}")
            
            # Build LED commands (same logic as playback screen - based on voltage)
            led_commands = []
            
            # Get voltage values for LED control
            v1a = float(record.get('V1A', 0))
            v1b = float(record.get('V1B', 0))
            v2a = float(record.get('V2A', 0))
            v2b = float(record.get('V2B', 0))
            v3a = float(record.get('V3A', 0))
            v3b = float(record.get('V3B', 0))
            v4a = float(record.get('V4A', 0))
            v4b = float(record.get('V4B', 0))
            
            # Determine LED colors based on voltage (same as playback screen)
            led_1a = self._get_voltage_color(v1a)
            led_1b = self._get_voltage_color(v1b)
            led_2a = self._get_voltage_color(v2a)
            led_2b = self._get_voltage_color(v2b)
            led_3a = self._get_voltage_color(v3a)
            led_3b = self._get_voltage_color(v3b)
            led_4a = self._get_voltage_color(v4a)
            led_4b = self._get_voltage_color(v4b)
            
            # Build individual LED commands (same as playback screen)
            led_commands = [
                f"LED_1A={led_1a}",
                f"LED_2A={led_2a}",
                f"LED_3A={led_3a}",
                f"LED_4A={led_4a}",
                f"LED_1B={led_1b}",
                f"LED_2B={led_2b}",
                f"LED_3B={led_3b}",
                f"LED_4B={led_4b}"
            ]
            
            # Debug: Print LED commands
            log_info(f"Mimic Screen: LED commands: {led_commands}")
            
            # Send LED commands with delays (same as playback screen)
            for i, cmd in enumerate(led_commands):
                serialWrite(cmd)
                if i < len(led_commands) - 1:  # Don't delay after last command
                    time.sleep(0.02)  # 20ms delay between commands
            
        except Exception as exc:
            log_error(f"Failed to send LED commands: {exc}")
    
    def _get_voltage_color(self, voltage):
        """Determine LED color based on voltage threshold (same as playback screen)."""
        if voltage < 151.5:
            return "Blue"      # Discharging
        elif voltage < 160.0:
            return "Yellow"    # Charging
        else:
            return "White"     # Fully charged

    # ---------------------------------------------------------------- start
    def startproc(self) -> None:
        log_info(f"Start Proc")
        """
        Launches the collector scripts in the background.
        Keeps Popen handles on the App instance so MainScreen EXIT can kill them.
        """
        app  = App.get_running_app()
        base = Path(self.mimic_directory) / "Mimic" / "Pi"   # ? cast to Path

        log_info("Starting telemetry subprocesses")
        
        # Check if scripts exist
        iss_telemetry_path = base / "iss_telemetry.py"
        tdrscheck_path = base / "TDRScheck.py"
        vvcheck_path = base / "VVcheck.py"
        checkcrew_path = base / "checkCrew.py"
        
        if not iss_telemetry_path.exists():
            log_error(f"iss_telemetry.py not found at {iss_telemetry_path}")
            return
            
        if not tdrscheck_path.exists():
            log_error(f"TDRScheck.py not found at {tdrscheck_path}")
            return
        if not vvcheck_path.exists():
            log_error(f"VVcheck.py not found at {vvcheck_path}")
            return
            
        if not checkcrew_path.exists():
            log_error(f"checkCrew.py not found at {checkcrew_path}")
            return
        
        try:
            # Start ISS telemetry process
            app.p = Popen(
                ["python", str(iss_telemetry_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            log_info(f"Started iss_telemetry.py (PID: {app.p.pid})")
            
            # Start TDRS check process
            app.TDRSproc = Popen(
                ["python", str(tdrscheck_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            log_info(f"Started TDRScheck.py (PID: {app.TDRSproc.pid})")
            
            # Start NASA Visiting Vehicles updater
            app.VVproc = Popen(
                ["python", str(vvcheck_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            log_info(f"Started VVcheck.py (PID: {app.VVproc.pid})")
            
            # Start ISS Crew updater
            app.crewproc = Popen(
                ["python", str(checkcrew_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            log_info(f"Started checkCrew.py (PID: {app.crewproc.pid})")
            
            
            # Check if processes started successfully
            if app.p.poll() is not None:
                stdout, stderr = app.p.communicate()
                log_error(f"iss_telemetry.py failed to start: {stderr}")
                app.p = None
                
            if app.TDRSproc.poll() is not None:
                stdout, stderr = app.TDRSproc.communicate()
                log_error(f"TDRScheck.py failed to start: {stderr}")
                app.TDRSproc = None
                
            if app.VVproc.poll() is not None:
                stdout, stderr = app.VVproc.communicate()
                log_error(f"VVcheck.py failed to start: {stderr}")
                app.VVproc = None
                
            if app.crewproc.poll() is not None:
                stdout, stderr = app.crewproc.communicate()
                log_error(f"checkCrew.py failed to start: {stderr}")
                app.crewproc = None
                
        except Exception as exc:
            log_error(f"Failed to start telemetry procs: {exc}")
            app.p = app.TDRSproc = app.VVproc = app.crewproc = None

    # ---------------------------------------------------------------- stop
    def killproc(self, *_):
        """
        Stops helper processes and flips mimicbutton ? False.
        Runs when EXIT is pressed or when ScreenManager leaves MimicScreen.
        """
        app = App.get_running_app()

        # optional: mark LS unsubscribed in your DB
        try:
            if hasattr(app, "db_cursor"):
                app.db_cursor.execute(
                    "INSERT OR IGNORE INTO telemetry "
                    "VALUES('Lightstreamer', '0', 'Unsubscribed', '0', 0)"
                )
        except Exception as exc:
            log_error(f"DB write failed: {exc}")

        for name in ("p", "TDRSproc", "VVproc", "crewproc"):
            proc = getattr(app, name, None)
            if not proc:
                continue
            try:
                proc.terminate(); proc.wait(timeout=3)
                log_info(f"{name} terminated.")
            except Exception as exc:
                log_error(f"Failed to kill {name}: {exc}")
            finally:
                setattr(app, name, None)

        app.mimicbutton = False

    # auto-cleanup when user leaves the screen
    def on_pre_leave(self):        # ScreenManager hook
        """
        Only kill processes when explicitly exiting mimic screen (via back button), 
        not when navigating to subscreens.
        """
        # Since the back button explicitly calls killproc(), we don't need to do anything here
        # The processes will only be killed when the user explicitly presses the back button
        log_info("Leaving mimic screen")
    
    def on_leave(self):
        """Called when leaving the screen."""
        # Don't stop mimic telemetry when navigating to subscreens
        # Only stop when explicitly leaving the mimic screen
        pass