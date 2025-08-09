from __future__ import annotations
from kivy.uix.screenmanager import Screen
import pathlib
from kivy.lang import Builder
from kivy.clock import Clock
from utils.logger import log_info, log_error
import sqlite3
from pathlib import Path
from ._base import MimicBase

kv_path = pathlib.Path(__file__).with_name("ECLSS_WRM_Screen.kv")
Builder.load_file(str(kv_path))

class ECLSS_WRM_Screen(MimicBase):
    """ECLSS WRM: urine tank, clean/waste water, process states and steps."""

    _update_event = None

    def on_enter(self):
        try:
            self.update_wrm_values(0)
            self._update_event = Clock.schedule_interval(self.update_wrm_values, 2)
            log_info("WRM: started updates (2s)")
        except Exception as exc:
            log_error(f"WRM on_enter failed: {exc}")

    def on_leave(self):
        try:
            if self._update_event is not None:
                Clock.unschedule(self._update_event)
                self._update_event = None
                log_info("WRM: stopped updates")
        except Exception as exc:
            log_error(f"WRM on_leave failed: {exc}")

    def _get_db_path(self) -> Path:
        shm = Path('/dev/shm/iss_telemetry.db')
        if shm.exists():
            return shm
        return Path.home() / '.mimic_data' / 'iss_telemetry.db'

    def _set_text(self, id_name: str, text: str):
        if id_name in self.ids:
            self.ids[id_name].text = text

    def update_wrm_values(self, _dt):
        try:
            db_path = self._get_db_path()
            if not db_path.exists():
                return
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute('select Value from telemetry')
            values = cur.fetchall()
            conn.close()

            # Tank levels
            self._set_text('UrineTank', f"{float(values[90][0]):.2f}")
            self._set_text('CleanWater', f"{float(values[93][0]):.2f}")
            self._set_text('WasteWater', f"{float(values[94][0]):.2f}")

            # Process states
            try:
                UrineProcessState = int(float(values[89][0]))
                urine_map = {
                    2: 'STOP', 4: 'SHTDWN', 8: 'MAINT', 16: 'NORM',
                    32: 'STBY', 64: 'IDLE', 128: 'INIT',
                }
                self._set_text('UrineProcessState', urine_map.get(UrineProcessState, 'n/a'))
            except Exception:
                self._set_text('UrineProcessState', 'n/a')

            try:
                WaterProcessState = int(float(values[91][0]))
                water_state_map = {1: 'STOP', 2: 'SHTDWN', 3: 'STBY', 4: 'PROC', 5: 'HOT SVC', 6: 'FLUSH', 7: 'WARM SHTDWN'}
                self._set_text('WaterProcessState', water_state_map.get(WaterProcessState, 'n/a'))
            except Exception:
                self._set_text('WaterProcessState', 'n/a')

            try:
                WaterProcessStep = int(float(values[92][0]))
                water_step_map = {0: 'NONE', 1: 'VENT', 2: 'HEATUP', 3: 'OURGE', 4: 'FLOW', 5: 'TEST', 6: 'TEST SV 1', 7: 'TEST SV 2', 8: 'SERVICE'}
                self._set_text('WaterProcessStep', water_step_map.get(WaterProcessStep, 'n/a'))
            except Exception:
                self._set_text('WaterProcessStep', 'n/a')

        except Exception as exc:
            log_error(f"WRM update failed: {exc}")
