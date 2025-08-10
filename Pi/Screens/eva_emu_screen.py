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

kv_path = pathlib.Path(__file__).with_name("EVA_EMU_Screen.kv")
Builder.load_file(str(kv_path))

class EVA_EMU_Screen(MimicBase):
    _update_event = None
    
    def on_enter(self):
        try:
            self.update_eva_emu_values(0)
            self._update_event = Clock.schedule_interval(self.update_eva_emu_values, 2)
            log_info("EVA_EMU: started updates (2s)")
        except Exception as exc:
            log_error(f"EVA_EMU on_enter failed: {exc}")
    
    def on_leave(self):
        try:
            if self._update_event:
                self._update_event.cancel()
                self._update_event = None
            log_info("EVA_EMU: stopped updates")
        except Exception as exc:
            log_error(f"EVA_EMU on_leave failed: {exc}")
    
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
    
    def update_eva_emu_values(self, _dt):
        try:
            db_path = self._get_db_path()
            if not db_path.exists():
                return
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute('select Value from telemetry')
            values = cur.fetchall()
            conn.close()
            
            # EVA EMU Telemetry - indices from database_initialize.py
            # PSA (Power Supply Assembly) - EMU 1 & 2
            psa_power_emu1 = float(values[61][0]) if values[61][0] else 0.0
            psa_current_emu1 = float(values[62][0]) if values[62][0] else 0.0
            psa_power_emu2 = float(values[63][0]) if values[63][0] else 0.0
            psa_current_emu2 = float(values[64][0]) if values[64][0] else 0.0
            
            # UIA (Utility Interface Assembly) - EMU 1 & 2
            uia_power_emu1 = float(values[67][0]) if values[67][0] else 0.0
            uia_current_emu1 = float(values[68][0]) if values[68][0] else 0.0
            uia_power_emu2 = float(values[69][0]) if values[69][0] else 0.0
            uia_current_emu2 = float(values[70][0]) if values[70][0] else 0.0
            
            # IRU (Inertial Reference Unit)
            iru_voltage = float(values[65][0]) if values[65][0] else 0.0
            iru_current = float(values[66][0]) if values[66][0] else 0.0
            
            # Update UI with formatted values
            self._set_text('UIApowerEMU1', f"{uia_power_emu1:.2f} V")
            self._set_text('UIApowerEMU2', f"{uia_power_emu2:.2f} V")
            self._set_text('UIAcurrentEMU1', f"{uia_current_emu1:.2f} A")
            self._set_text('UIAcurrentEMU2', f"{uia_current_emu2:.2f} A")
            
            self._set_text('PSApowerEMU1', f"{psa_power_emu1:.2f} V")
            self._set_text('PSApowerEMU2', f"{psa_power_emu2:.2f} V")
            self._set_text('PSAcurrentEMU1', f"{psa_current_emu1:.2f} A")
            self._set_text('PSAcurrentEMU2', f"{psa_current_emu2:.2f} A")
            
            self._set_text('IRUvoltage', f"{iru_voltage:.2f} V")
            self._set_text('IRUcurrent', f"{iru_current:.2f} A")
            
        except Exception as exc:
            log_error(f"EVA_EMU update failed: {exc}")
    
    def _set_text(self, widget_id: str, text: str):
        """Helper to safely set text on a widget"""
        try:
            if widget_id in self.ids:
                self.ids[widget_id].text = text
        except Exception:
            pass
