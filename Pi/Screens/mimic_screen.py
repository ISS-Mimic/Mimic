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
    def change_mimic_boolean(self, value: bool) -> None:
        """
        Bound in KV.  True ? transmit; False ? idle.
        Now directly controls mimic telemetry instead of just setting a boolean.
        """
        if value:
            self.start_mimic_telemetry()
        else:
            self.stop_mimic_telemetry()
        log_info(f"Change Mimic Boolean: {value}")
    changeMimicBoolean = change_mimic_boolean      # keep legacy name
    
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
            
            # Get all telemetry records ordered by timestamp
            cursor.execute("SELECT * FROM telemetry ORDER BY timestamp")
            rows = cursor.fetchall()
            
            if rows:
                # Convert to list of dictionaries for easier access
                columns = [description[0] for description in cursor.description]
                self._telemetry_data = []
                
                for row in rows:
                    record = dict(zip(columns, row))
                    self._telemetry_data.append(record)
                
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
            
            # Build telemetry command (same format as playback screen)
            telemetry_cmd = (
                f"PSARJ={record.get('PSARJ', 0.0):.1f} "
                f"SSARJ={record.get('SSARJ', 0.0):.1f} "
                f"PTRRJ={record.get('PTRRJ', 0.0):.1f} "
                f"STRRJ={record.get('STRRJ', 0.0):.1f} "
                f"B1B={record.get('B1B', 0.0):.1f} "
                f"B1A={record.get('B1A', 0.0):.1f} "
                f"B2B={record.get('B2B', 0.0):.1f} "
                f"B2A={record.get('B2A', 0.0):.1f} "
                f"B3B={record.get('B3B', 0.0):.1f} "
                f"B3A={record.get('B3A', 0.0):.1f} "
                f"B4B={record.get('B4B', 0.0):.1f} "
                f"B4A={record.get('B4A', 0.0):.1f} "
                f"AOS={record.get('AOS', 0)} "
                f"ISS={record.get('ISS', 0)} "
                f"Sgnt_el={record.get('Sgnt_el', 0.0):.1f} "
                f"Sgnt_xel={record.get('Sgnt_xel', 0.0):.1f} "
                f"Sgnt_xmit={record.get('Sgnt_xmit', 0)} "
                f"SASA_Xmit={record.get('SASA_Xmit', 0)} "
                f"SASA_AZ={record.get('SASA_AZ', 0.0):.1f} "
                f"SASA_EL={record.get('SASA_EL', 0.0):.1f}"
            )
            
            # Send telemetry command
            serialWrite(telemetry_cmd)
            
            # Send LED commands (same logic as playback screen)
            self._send_led_commands(record)
            
            # Move to next record (loop back to start)
            self._current_telemetry_index = (self._current_telemetry_index + 1) % len(self._telemetry_data)
            
        except Exception as exc:
            log_error(f"Failed to send mimic telemetry: {exc}")
    
    def _send_led_commands(self, record):
        """Send LED commands based on telemetry data."""
        try:
            # Build LED commands (same logic as playback screen)
            led_commands = []
            
            # Solar array 1A
            if record.get('B1A', 0) > 0:
                led_commands.append("LED_1A=Blue")
            else:
                led_commands.append("LED_1A=Off")
            
            # Solar array 1B
            if record.get('B1B', 0) > 0:
                led_commands.append("LED_1B=Blue")
            else:
                led_commands.append("LED_1B=Off")
            
            # Solar array 2A
            if record.get('B2A', 0) > 0:
                led_commands.append("LED_2A=Blue")
            else:
                led_commands.append("LED_2A=Off")
            
            # Solar array 2B
            if record.get('B2B', 0) > 0:
                led_commands.append("LED_2B=Blue")
            else:
                led_commands.append("LED_2B=Off")
            
            # Solar array 3A
            if record.get('B3A', 0) > 0:
                led_commands.append("LED_3A=Blue")
            else:
                led_commands.append("LED_3A=Off")
            
            # Solar array 3B
            if record.get('B3B', 0) > 0:
                led_commands.append("LED_3B=Blue")
            else:
                led_commands.append("LED_3B=Off")
            
            # Solar array 4A
            if record.get('B4A', 0) > 0:
                led_commands.append("LED_4A=Blue")
            else:
                led_commands.append("LED_4A=Off")
            
            # Solar array 4B
            if record.get('B4B', 0) > 0:
                led_commands.append("LED_4B=Blue")
            else:
                led_commands.append("LED_4B=Off")
            
            # Send LED commands with delays (same as playback screen)
            for i, cmd in enumerate(led_commands):
                serialWrite(cmd)
                if i < len(led_commands) - 1:  # Don't delay after last command
                    time.sleep(0.02)  # 20ms delay between commands
            
        except Exception as exc:
            log_error(f"Failed to send LED commands: {exc}")

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