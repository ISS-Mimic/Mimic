from __future__ import annotations

from pathlib import Path
import pathlib
import logging
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
    changeMimicBoolean = change_mimic_boolean      # keep legacy name

    # ---------------------------------------------------------------- start
    def startproc(self) -> None:
        """
        Launches the two collector scripts in the background.
        Keeps Popen handles on the App instance so MainScreen EXIT can kill them.
        """
        app  = App.get_running_app()
        base = Path(self.mimic_directory) / "Mimic" / "Pi"   # ? cast to Path

        log_info("Starting telemetry subprocesses")
        try:
            app.p        = Popen(["python", str(base / "iss_telemetry.py")])
            app.TDRSproc = Popen(["python", str(base / "TDRScheck.py")])
        except Exception as exc:
            log_error(f"Failed to start telemetry procs: {exc}")
            app.p = app.TDRSproc = None

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

        for name in ("p", "TDRSproc"):
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
        self.killproc()

