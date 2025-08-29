from __future__ import annotations
from kivy.uix.screenmanager import Screen
import pathlib
from pathlib import Path
import sqlite3
from kivy.lang import Builder
from kivy.clock import Clock
from ._base import MimicBase
from utils.logger import log_info, log_error

kv_path = pathlib.Path(__file__).with_name("CT_UHF_Screen.kv")
Builder.load_file(str(kv_path))

class CT_UHF_Screen(MimicBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._update_event = None
        
    def on_enter(self):
        """Start telemetry updates when entering the screen"""
        if self._update_event is None:
            self._update_event = Clock.schedule_interval(self.update_uhf_values, 1.0)
            log_info("CT UHF Screen: Started telemetry updates")
    
    def on_leave(self):
        """Stop telemetry updates when leaving the screen"""
        if self._update_event:
            Clock.unschedule(self._update_event)
            self._update_event = None
            log_info("CT UHF Screen: Stopped telemetry updates")
    
    def _get_db_path(self) -> Path:
        shm = Path('/dev/shm/iss_telemetry.db')
        if shm.exists():
            return shm
        return Path.home() / '.mimic_data' / 'iss_telemetry.db'
    
    def update_uhf_values(self, dt):
        """Update UHF screen telemetry values"""
        try:
            # Connect to telemetry database
            db_path = self._get_db_path()
            if not db_path.exists():
                log_error(f"CT UHF Screen: Database file not found at {db_path}")
                return
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute('select Value from telemetry')
            values = cur.fetchall()
            conn.close()
            
            # Extract UHF-related telemetry values
            uhf1_power = int(values[233][0])  # UHF 1 power status
            uhf2_power = int(values[234][0])  # UHF 2 power status
            uhf_frame_sync = int(values[235][0])  # UHF frame sync status
            
            # Update UHF 1 power status
            if uhf1_power == 0:
                self.ids.UHF1pwr.text = "Off-Ok"
            elif uhf1_power == 1:
                self.ids.UHF1pwr.text = "Not Off-Ok"
            elif uhf1_power == 2:
                self.ids.UHF1pwr.text = "Not Off-Failed"
            else:
                self.ids.UHF1pwr.text = "n/a"
            
            # Update UHF 2 power status
            if uhf2_power == 0:
                self.ids.UHF2pwr.text = "Off-Ok"
            elif uhf2_power == 1:
                self.ids.UHF2pwr.text = "Not Off-Ok"
            elif uhf2_power == 2:
                self.ids.UHF2pwr.text = "Not Off-Failed"
            else:
                self.ids.UHF2pwr.text = "n/a"
            
            # Update UHF frame sync status
            if uhf_frame_sync == 0:
                self.ids.UHFframeSync.text = "Unlocked"
            elif uhf_frame_sync == 1:
                self.ids.UHFframeSync.text = "Locked"
            else:
                self.ids.UHFframeSync.text = "n/a"
            
            conn.close()
            
        except Exception as e:
            log_error(f"CT UHF Screen update failed: {e}")
            if 'conn' in locals():
                conn.close()
