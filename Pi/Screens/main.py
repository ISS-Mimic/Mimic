from __future__ import annotations
import threading
import subprocess
import pathlib
import os
import math
from kivy.clock import Clock

from kivy.uix.screenmanager import Screen
from kivy.app import App
from kivy.lang import Builder

from utils.serial import serialWrite
from utils.logger import log_info, log_error

kv_path = pathlib.Path(__file__).with_name("MainScreen.kv")
Builder.load_file(str(kv_path))

class MainScreen(Screen):
    """
    Home screen. Handles navigation to other screens and the red EXIT button.
    """

    mimic_directory = pathlib.Path(__file__).resolve().parents[3]   # …/Mimic
    
    # ISS animation variables
    _iss1_x: float = 0.0
    _iss1_y: float = 0.75
    _iss1_size_x: float = 0.07
    _iss1_size_y: float = 0.07
    _iss1_starting: bool = True
    
    _iss2_x: float = 0.0
    _iss2_y: float = 0.75

    def killproc(self, *_):
        """
        EXIT button callback — guaranteed to shut everything down.
    
        * UI thread:   closes the window right away (app.stop()).
        * Worker thread: terminates helper processes, cleans temp files,
          then forces *hard* interpreter exit via `os._exit(0)`.
        """
    
        if getattr(self, "_exiting", False):
            return                      # double-click guard
        self._exiting = True
    
        app = App.get_running_app()
        app.stop()                      # ⇢ window disappears instantly
    
        # ------------------------------------------------------------
        # launch daemon thread to finish cleanup in background
        # ------------------------------------------------------------
        threading.Thread(
            target=self._background_cleanup_and_exit,
            daemon=True
        ).start()
    
    
    # ──────────────────────────────────────────────────────────────
    # runs in a daemon thread; UI already closed
    # ──────────────────────────────────────────────────────────────
    def _background_cleanup_and_exit(self):
        app = App.get_running_app()
    
        # 1) stop observer
        observer = getattr(app, "tty_observer", None)
        if observer:
            try:
                observer.stop()
                log_info("TTY observer stopped.")
            except Exception as exc:
                log_error(f"Error stopping observer: {exc}")
    
        # 2) terminate helper subprocesses
        for attr in (
            "p", "TDRSproc",
            "demo_proc", "disco_proc",
            "htv_proc", "oft2_proc",
        ):
            self._terminate_attr(app, attr)
    
        # 3) wipe temporary sqlite caches
        for db in pathlib.Path("/dev/shm").glob("*.db*"):
            try:
                db.unlink()
            except OSError as exc:
                log_error(f"Could not remove {db}: {exc}")
    
        # 4) done – force interpreter exit (bypasses lingering threads)
        os._exit(0)                     # ← never returns
    
    def on_pre_enter(self, *_):
        """Start ISS animations when entering the screen."""
        self._start_iss_animations()
    
    def on_pre_leave(self, *_):
        """Stop ISS animations when leaving the screen."""
        self._stop_iss_animations()
    
    def _start_iss_animations(self):
        """Start the ISS animation timers."""
        try:
            # Start the first ISS animation
            self._iss1_animation_event = Clock.schedule_interval(self._animate_iss1, 0.1)
            log_info("MainScreen: ISS animations started")
        except Exception as exc:
            log_error(f"Failed to start ISS animations: {exc}")
    
    def _stop_iss_animations(self):
        """Stop the ISS animation timers."""
        try:
            if hasattr(self, '_iss1_animation_event'):
                self._iss1_animation_event.cancel()
            if hasattr(self, '_iss2_animation_event'):
                self._iss2_animation_event.cancel()
            log_info("MainScreen: ISS animations stopped")
        except Exception as exc:
            log_error(f"Failed to stop ISS animations: {exc}")
    
    def _animate_iss1(self, dt):
        """Animate the first ISS icon (ISStiny)."""
        try:
            if self._iss1_x < 0.886:
                self._iss1_x += 0.007
                self._iss1_y = (math.sin(self._iss1_x * 30) / 18) + 0.75
                if hasattr(self, 'ids') and 'ISStiny' in self.ids:
                    self.ids.ISStiny.pos_hint = {"center_x": self._iss1_x, "center_y": self._iss1_y}
            else:
                if self._iss1_size_x <= 0.15:
                    self._iss1_size_x += 0.01
                    self._iss1_size_y += 0.01
                    if hasattr(self, 'ids') and 'ISStiny' in self.ids:
                        self.ids.ISStiny.size_hint = self._iss1_size_x, self._iss1_size_y
                else:
                    if self._iss1_starting:
                        # Start the second ISS animation
                        self._iss2_animation_event = Clock.schedule_interval(self._animate_iss2, 0.1)
                        self._iss1_starting = False
        except Exception as exc:
            log_error(f"Error in ISS1 animation: {exc}")
    
    def _animate_iss2(self, dt):
        """Animate the second ISS icon (ISStiny2)."""
        try:
            if hasattr(self, 'ids') and 'ISStiny2' in self.ids:
                self.ids.ISStiny2.size_hint = 0.07, 0.07
                self._iss2_x += 0.007
                self._iss2_y = (math.sin(self._iss2_x * 30) / 18) + 0.75
                if self._iss2_x > 1:
                    self._iss2_x -= 1.0
                self.ids.ISStiny2.pos_hint = {"center_x": self._iss2_x, "center_y": self._iss2_y}
        except Exception as exc:
            log_error(f"Error in ISS2 animation: {exc}")
    
    
    # helper stays unchanged
    @staticmethod
    def _terminate_attr(app: App, attr_name: str) -> None:
        proc = getattr(app, attr_name, None)
        if not proc:
            return
        try:
            proc.terminate()
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        except Exception as exc:
            log_error(f"Failed to terminate {attr_name}: {exc}")
        finally:
            setattr(app, attr_name, None)
            log_info(f"{attr_name} terminated.")
