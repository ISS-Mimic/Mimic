from __future__ import annotations
from kivy.uix.screenmanager import Screen
import pathlib
from kivy.lang import Builder
from ._base import MimicBase
import sqlite3
import platform
from pathlib import Path
from kivy.clock import Clock
from utils.logger import log_info, log_error

kv_path = pathlib.Path(__file__).with_name("CT_Screen.kv")
Builder.load_file(str(kv_path))

class CT_Screen(MimicBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._update_event = None
        
    def on_enter(self):
        """Start telemetry updates when entering the screen"""
        if self._update_event is None:
            self._update_event = Clock.schedule_interval(self.update_ct_values, 1.0)
            log_info("CT Screen: Started telemetry updates")
    
    def on_leave(self):
        """Stop telemetry updates when leaving the screen"""
        if self._update_event:
            Clock.unschedule(self._update_event)
            self._update_event = None
            log_info("CT Screen: Stopped telemetry updates")
    
    def _get_db_path(self):
        """Get the database path based on platform"""
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
    
    def update_ct_values(self, dt):
        """Update CT screen telemetry values"""
        try:
            # Connect to telemetry database
            db_path = self._get_db_path()
            if not db_path.exists():
                log_error(f"CT Screen: Database file not found at {db_path}")
                return
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute('select Value from telemetry')
            values = cur.fetchall()
            
            if not values:
                log_error(f"CT Screen: Not enough data in database")
                conn.close()
                return
            
            # Extract CT-related telemetry values
            aos = int(values[12][0])  # Acquisition of Signal (index 12)
            sasa1_active = int(values[53][0])  # SASA 1 active status
            sasa2_active = int(values[52][0])  # SASA 2 active status
            uhf1_power = int(values[233][0])   # UHF 1 power (0=off, 1=on, 3=failed)
            uhf2_power = int(values[234][0])   # UHF 2 power (0=off, 1=on, 3=failed)
            sgant_transmit = int(values[41][0])

            print(aos, sasa1_active, sasa2_active, uhf1_power, uhf2_power, sgant_transmit)

            # Update SGANT radio indicators based on AOS status
            if sgant_transmit == 1 and aos == 1:
                self.ids.sgant1_radio.color = (1, 1, 1, 1)
                self.ids.sgant2_radio.color = (1, 1, 1, 1)
            else:
                self.ids.sgant1_radio.color = (0, 0, 0, 0)
                self.ids.sgant2_radio.color = (0, 0, 0, 0)
            
            # Update SASA 1 radio indicator
            if sasa1_active == 1 and aos == 1:
                self.ids.sasa1_radio.color = (1, 1, 1, 1)
            elif sasa1_active == 1 and aos == 0:
                self.ids.sasa1_radio.color = (0, 0, 0, 0)
            elif sasa1_active == 0:
                self.ids.sasa1_radio.color = (0, 0, 0, 0)
            elif aos == 0:
                self.ids.sasa1_radio.color = (0, 0, 0, 0)
            
            # Update SASA 2 radio indicator
            if sasa2_active == 1 and aos == 1:
                self.ids.sasa2_radio.color = (1, 1, 1, 1)
            elif sasa2_active == 1 and aos == 0:
                self.ids.sasa2_radio.color = (0, 0, 0, 0)
            elif sasa2_active == 0:
                self.ids.sasa2_radio.color = (0, 0, 0, 0)
            elif aos == 0:
                self.ids.sasa2_radio.color = (0, 0, 0, 0)
            
            # Update UHF 1 radio indicator
            if uhf1_power == 1 and aos == 1:
                self.ids.uhf1_radio.color = (1, 1, 1, 1)
            elif uhf1_power == 1 and aos == 0:
                self.ids.uhf1_radio.color = (1, 0, 0, 1)  # Red when no AOS
            elif uhf1_power == 0:
                self.ids.uhf1_radio.color = (0, 0, 0, 0)
            
            # Update UHF 2 radio indicator
            if uhf2_power == 1 and aos == 1:
                self.ids.uhf2_radio.color = (1, 1, 1, 1)
            elif uhf2_power == 1 and aos == 0:
                self.ids.uhf2_radio.color = (1, 0, 0, 1)  # Red when no AOS
            elif uhf2_power == 0:
                self.ids.uhf2_radio.color = (0, 0, 0, 0)
            
            conn.close()
            
        except Exception as e:
            log_error(f"CT Screen update failed: {e}")
            if 'conn' in locals():
                conn.close()
