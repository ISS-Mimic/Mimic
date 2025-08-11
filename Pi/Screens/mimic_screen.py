from __future__ import annotations

from pathlib import Path
import pathlib
import subprocess
from subprocess import Popen
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty
from kivy.lang import Builder
from kivy.app import App

from ._base import MimicBase                    # gives mimic_directory + signalcolor
from utils.logger import log_info, log_error

# -- load KV that sits next to this file -------------------------------------
kv_path = pathlib.Path(__file__).with_name("MimicScreen.kv")
Builder.load_file(str(kv_path))

class MimicScreen(MimicBase):
    log_info("MimicScreen loaded")
    """
    Live ISS telemetry hub.
    Starts / stops iss_telemetry.py and TDRScheck.py, toggled by a
    'Mimic' button in the GUI.
    """

    # ------------------------------------------------------------------- UI
    def change_mimic_boolean(self, value: bool) -> None:
        """
        Bound in KV.  True ? transmit; False ? idle.
        Mirrors the state on the App instance (no global).
        """
        App.get_running_app().mimicbutton = value
        log_info(f"Change Mimic Boolean: {value}")
    changeMimicBoolean = change_mimic_boolean      # keep legacy name

    # ---------------------------------------------------------------- start
    def startproc(self) -> None:
        log_info(f"Start Proc")
        """
        Launches the two collector scripts in the background.
        Keeps Popen handles on the App instance so MainScreen EXIT can kill them.
        """
        app  = App.get_running_app()
        base = Path(self.mimic_directory) / "Mimic" / "Pi"   # ? cast to Path

        log_info("Starting telemetry subprocesses")
        
        # Check if scripts exist
        iss_telemetry_path = base / "iss_telemetry.py"
        tdrscheck_path = base / "TDRScheck.py"
        vvcheck_path = base / "VVcheck.py"
        
        if not iss_telemetry_path.exists():
            log_error(f"iss_telemetry.py not found at {iss_telemetry_path}")
            return
            
        if not tdrscheck_path.exists():
            log_error(f"TDRScheck.py not found at {tdrscheck_path}")
            return
        if not vvcheck_path.exists():
            log_error(f"VVcheck.py not found at {vvcheck_path}")
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
                
        except Exception as exc:
            log_error(f"Failed to start telemetry procs: {exc}")
            app.p = app.TDRSproc = app.VVproc = None

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

        for name in ("p", "TDRSproc", "VVproc"):
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