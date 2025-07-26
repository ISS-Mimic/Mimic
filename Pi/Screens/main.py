from __future__ import annotations
import threading                 # ? add
import subprocess                # ? add
import pathlib                   # ? already needed for kv load
import os                        # ? add
import logging                   # for log_info / log_error aliases

from kivy.uix.screenmanager import Screen
from kivy.app import App
from kivy.lang import Builder

from utils.serial import serialWrite

log_info  = logging.getLogger("MyLogger").info
log_error = logging.getLogger("MyLogger").error

kv_path = pathlib.Path(__file__).with_name("MainScreen.kv")
Builder.load_file(str(kv_path))

class MainScreen(Screen):
    """
    Home screen. Handles the manual-control toggle and the red EXIT button.
    """

    mimic_directory = pathlib.Path(__file__).resolve().parents[3]   # …/Mimic

    # ──────────────────────────────────────────────────────────────
    # Manual-control toggle (called from kv)
    # ──────────────────────────────────────────────────────────────
    def change_manual_control(self, value: bool) -> None:
        App.get_running_app().manual_control = value

    changeManualControlBoolean = change_manual_control   # ← kv compatibility
    
    def killproc(self, *_):
        """
        Red EXIT button callback — guaranteed to shut everything down.
    
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
