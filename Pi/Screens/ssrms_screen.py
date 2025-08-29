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

            # Operating Base (values[261]) A/B
            OperatingBase = int(float(values[261][0]))
            if OperatingBase == 0:
                self.ids.OperatingBase.text = "LEE A"
            elif OperatingBase == 5:
                self.ids.OperatingBase.text = "LEE B"
            else:
                self.ids.OperatingBase.text = "n/a"

            # Tip LEE status (values[269])
            TipLEEstatus = int(float(values[269][0]))
            if TipLEEstatus == 0:
                self.ids.TipLEEstatus.text = "Released"
            elif TipLEEstatus == 1:
                self.ids.TipLEEstatus.text = "Captive"
            elif TipLEEstatus == 2:
                self.ids.TipLEEstatus.text = "Captured"
            else:
                self.ids.TipLEEstatus.text = "n/a"

            # Decode CSASSRMS001: SACS operating base in bits 6..9
            try:
                packed_csassrms001 = int(float(values[259][0]))
                sacs_operating_base = (packed_csassrms001 >> 6) & 0xF
                sacs_map = {0: "LEE A", 5: "LEE B"}
                self.ids.SACSopBase.text = sacs_map.get(sacs_operating_base, "n/a")
            except Exception:
                self.ids.SACSopBase.text = "n/a"

            # Joint angles
            self.ids.ShoulderRoll.text = f"{float(values[262][0]):.2f} deg"
            self.ids.ShoulderYaw.text = f"{float(values[263][0]):.2f} deg"
            self.ids.ShoulderPitch.text = f"{float(values[264][0]):.2f} deg"
            self.ids.ElbowPitch.text = f"{float(values[265][0]):.2f} deg"
            self.ids.WristRoll.text = f"{float(values[268][0]):.2f} deg"
            self.ids.WristYaw.text = f"{float(values[267][0]):.2f} deg"
            self.ids.WristPitch.text = f"{float(values[266][0]):.2f} deg"

            # Decode CSAMBA00003: LEE stop/speed/hot in bits 6.., 4.., 3
            try:
                packed_csamaba00003 = int(float(values[294][0]))
                lee_stop = (packed_csamaba00003 >> 6) & 0x3
                lee_speed = (packed_csamaba00003 >> 4) & 0x3
                lee_hot = (packed_csamaba00003 >> 3) & 0x1
                stop_map = {1: "Soft Stop", 2: "Hard Stop"}
                speed_map = {1: "Slow", 2: "Fast"}
                hot_map = {0: "Null", 1: "Hot"}
                if 'SSRMS_LEE_Stop_Condition' in self.ids:
                    self.ids.SSRMS_LEE_Stop_Condition.text = stop_map.get(lee_stop, "n/a")
                if 'SSRMS_LEE_Run_Speed' in self.ids:
                    self.ids.SSRMS_LEE_Run_Speed.text = speed_map.get(lee_speed, "n/a")
                if 'SSRMS_LEE_Hot' in self.ids:
                    self.ids.SSRMS_LEE_Hot.text = hot_map.get(lee_hot, "Null")
            except Exception:
                if 'SSRMS_LEE_Stop_Condition' in self.ids:
                    self.ids.SSRMS_LEE_Stop_Condition.text = "n/a"
                if 'SSRMS_LEE_Run_Speed' in self.ids:
                    self.ids.SSRMS_LEE_Run_Speed.text = "n/a"
                if 'SSRMS_LEE_Hot' in self.ids:
                    self.ids.SSRMS_LEE_Hot.text = "n/a"


            # Base location (values[260]) per mapping from GUI
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
