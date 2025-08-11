from __future__ import annotations

import pathlib, time, threading, logging
from pathlib import Path
from subprocess import Popen, CalledProcessError
from typing import Optional, Union, List

from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.clock import Clock
from kivy.app import App

from ._base import MimicBase            # gives mimic_directory + signalcolor
from utils.logger import log_info, log_error   # if you re-exported these; else import logging
from utils.serial import serialWrite

# ── load KV next to this file ──────────────────────────────────────────────
kv_path = pathlib.Path(__file__).with_name("Playback_Screen.kv")
Builder.load_file(str(kv_path))

# ───────────────────────────────────────────────────────────────────────────
class Playback_Screen(MimicBase):
    """
    Pick a USB stick or canned demo (HTV / OFT-2 / Disco) and run playback.
    """

    mimic_directory = StringProperty(
        str(pathlib.Path(__file__).resolve().parents[3])   # /home/pi/Mimic
    )
    usb_drives: set[str] = set()

    # ------------------------------------------------------------------ init
    def __init__(self, **kw):
        super().__init__(**kw)
        self.usb_drives = self._get_mount_points()
        self._start_usb_monitor()
        Clock.schedule_once(self._update_dropdown)

    # ---------------------------------------------------------------- USB IO
    @staticmethod
    def _get_mount_points() -> set[str]:
        media_dir = pathlib.Path("/media/pi")
        if not media_dir.is_dir():
            return set()
        try:
            return {p.name for p in media_dir.iterdir() if p.is_dir()}
        except Exception as exc:
            log_error(f"USB scan failed: {exc}")
            return set()

    def _usb_monitor_loop(self) -> None:
        prev = self.usb_drives
        while True:
            curr = self._get_mount_points()
            if curr != prev:
                self.usb_drives = curr
                Clock.schedule_once(self._update_dropdown)
                prev = curr
            time.sleep(5)

    def _start_usb_monitor(self) -> None:
        threading.Thread(target=self._usb_monitor_loop, daemon=True).start()

    def _update_dropdown(self, _dt) -> None:
        sp = self.ids.playback_dropdown
        sp.values = [f"{d} (USB)" for d in sorted(self.usb_drives)] + ["HTV", "OFT-2"]

    # bound in KV
    def on_dropdown_select(self, value: str) -> None:
        log_info(f"Playback selected: {value}")

    # ---------------------------------------------------- proc helpers
    def _launch(self, cmd: Union[str, List[str]], attr: str, nice: str):
        app = App.get_running_app()
        if getattr(app, attr, None):
            log_info(f"{nice} already running.")
            return
        try:
            proc = Popen([cmd] if isinstance(cmd, str) else cmd)
            setattr(app, attr, proc)
            log_info(f"{nice} started.")
        except (OSError, CalledProcessError) as exc:
            log_error(f"Failed to start {nice}: {exc}")
            setattr(app, attr, None)

    def _terminate(self, attr: str, nice: str):
        proc: Optional[Popen] = getattr(App.get_running_app(), attr, None)
        if not proc:
            return
        try:
            proc.terminate(); proc.wait(timeout=3)
            log_info(f"{nice} stopped.")
        except Exception as exc:
            log_error(f"Failed to stop {nice}: {exc}")
        finally:
            setattr(App.get_running_app(), attr, None)

    # ---------------------------------------------------- KV callbacks
    def start_disco(self):  
        script = Path(self.mimic_directory) / "Mimic/Pi/RecordedData/disco.sh"
        self._launch(str(script), "disco_proc", "Disco demo")
    
    def stop_disco(self):   
        self._terminate("disco_proc", "Disco demo")

    def start_demo_orbit(self):
        base   = Path(self.mimic_directory) / "Mimic/Pi/RecordedData"
        cmd    = [ str(base / "playback.out"), str(base / "OFT2") ]
        self._launch(cmd, "demo_proc", "Standard orbit demo")
    
    def stop_demo_orbit(self): 
        self._terminate("demo_proc", "Standard orbit demo")

    def start_htv(self):
        script = Path(self.mimic_directory) / "Mimic/Pi/RecordedData/demoHTVOrbit.sh"
        self._launch(str(script), "htv_proc", "HTV orbit demo") 
    
    def stop_htv(self):
        self._terminate("htv_proc", "HTV orbit demo")
    
    def start_oft2(self):   
        script = Path(self.mimic_directory) / "Mimic/Pi/RecordedData/demoOFT2.sh"
        self._launch(str(script), "oft2_proc", "OFT-2 orbit demo")
    
    def stop_oft2(self):
        self._terminate("oft2_proc", "OFT-2 orbit demo")
