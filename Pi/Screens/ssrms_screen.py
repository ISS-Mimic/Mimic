from __future__ import annotations
from kivy.uix.screenmanager import Screen
import pathlib
from kivy.lang import Builder
from kivy.clock import Clock
from utils.logger import log_info, log_error
import sqlite3
from pathlib import Path
from ._base import MimicBase

kv_path = pathlib.Path(__file__).with_name("SSRMS_Screen.kv")
Builder.load_file(str(kv_path))

class SSRMS_Screen(MimicBase):
    """SSRMS (Canadarm2) status screen: base/LEE states and joint angles."""

    _update_event = None

    def on_enter(self):
        try:
            self.update_ssrms_values(0)
            self._update_event = Clock.schedule_interval(self.update_ssrms_values, 2)
            log_info("SSRMS: started updates (2s)")
        except Exception as exc:
            log_error(f"SSRMS on_enter failed: {exc}")

    def on_leave(self):
        try:
            if self._update_event is not None:
                Clock.unschedule(self._update_event)
                self._update_event = None
                log_info("SSRMS: stopped updates")
        except Exception as exc:
            log_error(f"SSRMS on_leave failed: {exc}")

    def _get_db_path(self) -> Path:
        shm = Path('/dev/shm/iss_telemetry.db')
        if shm.exists():
            return shm
        return Path.home() / '.mimic_data' / 'iss_telemetry.db'

    def update_ssrms_values(self, _dt):
        try:
            db_path = self._get_db_path()
            if not db_path.exists():
                return
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute('select Value from telemetry')
            values = cur.fetchall()
            conn.close()

            # Operating Base (values[102]) A/B
            OperatingBase = int(float(values[261][0]))
            if OperatingBase == 1:
                self.ids.OperatingBase.text = "LEE A"
            elif OperatingBase == 2:
                self.ids.OperatingBase.text = "LEE B"
            else:
                self.ids.OperatingBase.text = "n/a"

            # Tip LEE status (values[103])
            TipLEEstatus = int(float(values[269][0]))
            if TipLEEstatus == 1:
                self.ids.TipLEEstatus.text = "Released"
            elif TipLEEstatus == 2:
                self.ids.TipLEEstatus.text = "Captive"
            elif TipLEEstatus == 3:
                self.ids.TipLEEstatus.text = "Captured"
            else:
                self.ids.TipLEEstatus.text = "n/a"

            # SACS operating base (values[104]) A/B
            SACSopBase = int(float(values[259][0]))
            if SACSopBase == 1:
                self.ids.SACSopBase.text = "LEE A"
            elif SACSopBase == 2:
                self.ids.SACSopBase.text = "LEE B"
            else:
                self.ids.SACSopBase.text = "n/a"

            # Joint angles (values[105..110]? per GUI usage order)
            self.ids.ShoulderRoll.text = f"{float(values[262][0]):.2f} deg"
            self.ids.ShoulderYaw.text = f"{float(values[263][0]):.2f} deg"
            self.ids.ShoulderPitch.text = f"{float(values[264][0]):.2f} deg"
            self.ids.ElbowPitch.text = f"{float(values[265][0]):.2f} deg"
            self.ids.WristRoll.text = f"{float(values[268][0]):.2f} deg"
            self.ids.WristYaw.text = f"{float(values[267][0]):.2f} deg"
            self.ids.WristPitch.text = f"{float(values[266][0]):.2f} deg"

            # Base location (values[112]) per mapping from GUI
            BaseLocation = int(float(values[260][0]))
            base_map = {
                1: "Lab",
                2: "Node 3",
                4: "Node 2",
                7: "MBS PDGF 1",
                8: "MBS PDGF 2",
                11: "MBS PDGF 3",
                13: "MBS PDGF 4",
                14: "FGB",
                16: "POA",
                19: "SSRMS Tip LEE",
                63: "Undefined",
            }
            self.ids.BaseLocation.text = base_map.get(BaseLocation, "n/a")

        except Exception as exc:
            log_error(f"SSRMS update failed: {exc}")
