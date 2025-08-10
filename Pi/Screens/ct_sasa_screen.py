from __future__ import annotations
from kivy.uix.screenmanager import Screen
import pathlib
import sqlite3
import platform
from pathlib import Path
from kivy.lang import Builder
from kivy.clock import Clock
from ._base import MimicBase
from utils.logger import log_info, log_error

kv_path = pathlib.Path(__file__).with_name("CT_SASA_Screen.kv")
Builder.load_file(str(kv_path))

class CT_SASA_Screen(MimicBase):
    _update_event = None
    
    def on_enter(self):
        try:
            self.update_ct_sasa_values(0)
            self._update_event = Clock.schedule_interval(self.update_ct_sasa_values, 2)
            log_info("CT_SASA: started updates (2s)")
        except Exception as exc:
            log_error(f"CT_SASA on_enter failed: {exc}")
    
    def on_leave(self):
        try:
            if self._update_event:
                self._update_event.cancel()
                self._update_event = None
            log_info("CT_SASA: stopped updates")
        except Exception as exc:
            log_error(f"CT_SASA on_leave failed: {exc}")
    
    def _get_db_path(self) -> Path:
        # Cross-platform database path
        if platform.system() == "Windows":
            # On Windows, use home directory
            base_path = Path.home() / '.mimic_data'
            base_path.mkdir(exist_ok=True)  # Ensure directory exists
            return base_path / 'iss_telemetry.db'
        else:
            # On Linux/Unix, use /dev/shm
            shm = Path('/dev/shm/iss_telemetry.db')
            if shm.exists():
                return shm
            return Path.home() / '.mimic_data' / 'iss_telemetry.db'
    
    def update_ct_sasa_values(self, _dt):
        try:
            db_path = self._get_db_path()
            if not db_path.exists():
                return
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute('select Value from telemetry')
            values = cur.fetchall()
            conn.close()
            
            # CT SASA Telemetry - indices from database_initialize.py
            # Active SASA (which SASA is currently active)
            active_sasa = str((values[54])[0]) if values[54][0] else "0"
            
            # SASA 1 (RFG1) - Status, Azimuth, Elevation
            sasa1_status = str((values[53])[0]) if values[53][0] else "0"
            sasa1_azimuth = "{:.2f}".format(float((values[18])[0])) if values[18][0] else "0.00"
            sasa1_elev = "{:.2f}".format(float((values[14])[0])) if values[14][0] else "0.00"
            
            # SASA 2 (RFG2) - Status, Azimuth, Elevation
            sasa2_status = str((values[52])[0]) if values[52][0] else "0"
            sasa2_azimuth = "{:.2f}".format(float((values[51])[0])) if values[51][0] else "0.00"
            sasa2_elev = "{:.2f}".format(float((values[50])[0])) if values[50][0] else "0.00"
            
            # Update UI with values
            self._set_text('ActiveString', str(active_sasa))
            
            # Update RFG1 (SASA 1) status with proper text mapping
            if int(sasa1_status) == 0:
                self._set_text('RFG1status', "Off-Ok")
            elif int(sasa1_status) == 1:
                self._set_text('RFG1status', "Not Off-Ok")
            elif int(sasa1_status) == 2:
                self._set_text('RFG1status', "Not Off-Failed")
            else:
                self._set_text('RFG1status', "n/a")
            
            self._set_text('RFG1azimuth', str(sasa1_azimuth))
            self._set_text('RFG1elev', str(sasa1_elev))
            
            # Update RFG2 (SASA 2) status with proper text mapping
            if int(sasa2_status) == 0:
                self._set_text('RFG2status', "Off-Ok")
            elif int(sasa2_status) == 1:
                self._set_text('RFG2status', "Not Off-Ok")
            elif int(sasa2_status) == 2:
                self._set_text('RFG2status', "Not Off-Failed")
            else:
                self._set_text('RFG2status', "n/a")
            
            self._set_text('RFG2azimuth', str(sasa2_azimuth))
            self._set_text('RFG2elev', str(sasa2_elev))
            
        except Exception as exc:
            log_error(f"CT_SASA update failed: {exc}")
    
    def _set_text(self, widget_id: str, text: str):
        """Helper to safely set text on a widget"""
        try:
            if widget_id in self.ids:
                self.ids[widget_id].text = text
        except Exception:
            pass
