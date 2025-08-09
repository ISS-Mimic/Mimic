from __future__ import annotations
from kivy.uix.screenmanager import Screen
import pathlib
from kivy.lang import Builder
from kivy.clock import Clock
from utils.logger import log_info, log_error
import sqlite3
from pathlib import Path
from ._base import MimicBase

kv_path = pathlib.Path(__file__).with_name("TCS_Screen.kv")
Builder.load_file(str(kv_path))

class TCS_Screen(MimicBase):
    """Thermal Control System screen: reads values from telemetry DB and updates labels."""

    _update_event = None

    def on_enter(self):
        try:
            self.update_tcs_values(0)
            self._update_event = Clock.schedule_interval(self.update_tcs_values, 2)
            log_info("TCS: started updates (2s)")
        except Exception as exc:
            log_error(f"TCS on_enter failed: {exc}")

    def on_leave(self):
        try:
            if self._update_event is not None:
                Clock.unschedule(self._update_event)
                self._update_event = None
                log_info("TCS: stopped updates")
        except Exception as exc:
            log_error(f"TCS on_leave failed: {exc}")

    def _get_db_path(self) -> Path:
        shm = Path('/dev/shm/iss_telemetry.db')
        if shm.exists():
            return shm
        return Path.home() / '.mimic_data' / 'iss_telemetry.db'

    def update_tcs_values(self, _dt):
        try:
            db_path = self._get_db_path()
            if not db_path.exists():
                return
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute('select Value from telemetry')
            values = cur.fetchall()
            conn.close()

            # Map values to screen (indices from GUI.py)
            ptrrj = "{:.2f}".format(float(values[2][0]))
            strrj = "{:.2f}".format(float(values[3][0]))
            self.ids.ptrrj_value.text = ptrrj + "deg"
            self.ids.strrj_value.text = strrj + "deg"

            # SW mode mapping
            SW_MODE_MAP = {
                1: "STANDBY",
                2: "RESTART",
                3: "CHECKOUT",
                4: "DIRECTED POS",
                5: "AUTOTRACK",
                6: "BLIND",
                7: "SHUTDOWN",
                8: "SWITCHOVER",
            }

            SWmode_loopA = int(float(values[190][0])) if len(values) > 190 else 0
            SWmode_loopB = int(float(values[191][0])) if len(values) > 191 else 0
            self.ids.SWmode_loopA.text = SW_MODE_MAP.get(SWmode_loopA, "UNKNOWN")
            self.ids.SWmode_loopB.text = SW_MODE_MAP.get(SWmode_loopB, "UNKNOWN")

            # NH3 flows/pressures/temps (indices per original GUI writes)
            self.ids.NH3flow_loopA.text = str(values[192][0])
            self.ids.NH3flow_loopB.text = str(values[193][0])
            self.ids.NH3outletPress_loopA.text = str(values[194][0])
            self.ids.NH3outletPress_loopB.text = str(values[195][0])
            self.ids.NH3outletTemp_loopA.text = str(values[196][0])
            self.ids.NH3outletTemp_loopB.text = str(values[197][0])

        except Exception as exc:
            log_error(f"TCS update failed: {exc}")
