from __future__ import annotations
from kivy.uix.screenmanager import Screen
import pathlib
from kivy.lang import Builder
from kivy.clock import Clock
from utils.logger import log_info, log_error
import sqlite3
from pathlib import Path
from ._base import MimicBase

kv_path = pathlib.Path(__file__).with_name("ECLSS_IATCS_Screen.kv")
Builder.load_file(str(kv_path))

class ECLSS_IATCS_Screen(MimicBase):
    """IATCS: Loop temps, water levels, air-control states for Lab/Node2/Node3."""

    _update_event = None

    def on_enter(self):
        try:
            self.update_iatcs_values(0)
            self._update_event = Clock.schedule_interval(self.update_iatcs_values, 2)
            log_info("IATCS: started updates (2s)")
        except Exception as exc:
            log_error(f"IATCS on_enter failed: {exc}")

    def on_leave(self):
        try:
            if self._update_event is not None:
                Clock.unschedule(self._update_event)
                self._update_event = None
                log_info("IATCS: stopped updates")
        except Exception as exc:
            log_error(f"IATCS on_leave failed: {exc}")

    def _get_db_path(self) -> Path:
        shm = Path('/dev/shm/iss_telemetry.db')
        if shm.exists():
            return shm
        return Path.home() / '.mimic_data' / 'iss_telemetry.db'

    def _set_text(self, id_name: str, text: str):
        if id_name in self.ids:
            self.ids[id_name].text = text

    def _map_ac(self, val: int) -> str:
        return {
            0: 'RESET', 1: 'DRAIN', 2: 'DRYOUT', 3: 'EIB OFF',
            4: 'OFF', 5: 'ON', 6: 'STARTUP', 7: 'TEST2',
        }.get(val, 'n/a')

    def update_iatcs_values(self, _dt):
        try:
            db_path = self._get_db_path()
            if not db_path.exists():
                return
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute('select Value from telemetry')
            values = cur.fetchall()
            conn.close()

            # Lab
            self._set_text('LTwater_Lab', f"{float(values[192][0]):.2f}")
            self._set_text('MTwater_Lab', f"{float(values[193][0]):.2f}")
            self._set_text('FluidTempAir_Lab', f"{float(values[197][0]):.2f}")
            self._set_text('FluidTempAv_Lab', f"{float(values[196][0]):.2f}")
            try:
                self._set_text('AC_LabPort', self._map_ac(int(float(values[200][0]))))
            except Exception:
                self._set_text('AC_LabPort', 'n/a')
            try:
                self._set_text('AC_LabStbd', self._map_ac(int(float(values[201][0]))))
            except Exception:
                self._set_text('AC_LabStbd', 'n/a')

            # Node 2
            self._set_text('LTwater_Node2', f"{float(values[82][0]):.2f}")
            self._set_text('MTwater_Node2', f"{float(values[81][0]):.2f}")
            self._set_text('FluidTempAir_Node2', f"{float(values[84][0]):.2f}")
            self._set_text('FluidTempAv_Node2', f"{float(values[85][0]):.2f}")
            try:
                self._set_text('AC_Node2', self._map_ac(int(float(values[83][0]))))
            except Exception:
                self._set_text('AC_Node2', 'n/a')

            # Node 3
            self._set_text('LTwater_Node3', f"{float(values[101][0]):.2f}")
            self._set_text('MTwater_Node3', f"{float(values[99][0]):.2f}")
            self._set_text('FluidTempAir_Node3', f"{float(values[98][0]):.2f}")
            self._set_text('FluidTempAv_Node3', f"{float(values[97][0]):.2f}")
            try:
                self._set_text('AC_Node3', self._map_ac(int(float(values[100][0]))))
            except Exception:
                self._set_text('AC_Node3', 'n/a')

        except Exception as exc:
            log_error(f"IATCS update failed: {exc}")
