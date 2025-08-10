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

kv_path = pathlib.Path(__file__).with_name("CT_SGANT_Screen.kv")
Builder.load_file(str(kv_path))

class CT_SGANT_Screen(MimicBase):
    def on_enter(self):
        """Called when the screen is entered - start updating values"""
        super().on_enter()
        # Schedule updates every 2 seconds
        Clock.schedule_interval(self.update_sgant_values, 2.0)
    
    def on_leave(self):
        """Called when the screen is left - stop updating values"""
        super().on_leave()
        # Cancel scheduled updates
        Clock.unschedule(self.update_sgant_values)
    
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
    
    def update_sgant_values(self, dt):
        """Update SGANT telemetry values from database"""
        try:
            db_path = self._get_db_path()
            if not db_path.exists():
                log_error(f"Database file not found: {db_path}")
                return
            
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            
            # Get all telemetry values
            cur.execute("SELECT value FROM telemetry ORDER BY id")
            values = cur.fetchall()
            
            if len(values) < 42:  # Need at least 42 values for kuband_transmit
                log_error(f"Not enough telemetry values: {len(values)}")
                conn.close()
                return
            
            # Extract SGANT values using indices from database_initialize.py
            sgant_elevation = float(values[15][0]) if values[15][0] else 0.0
            sgant_xelevation = float(values[17][0]) if values[17][0] else 0.0
            sgant_transmit = float(values[41][0]) if values[41][0] else 0.0
            aos = float(values[12][0]) if values[12][0] else 0.0
            
            # Update SGANT dish angle
            self._set_text(self.ids.sgant_dish, 'angle', float(sgant_elevation))
            
            # Update elevation display
            self._set_text(self.ids.sgant_elevation, 'text', "{:.2f}".format(float(sgant_elevation)))
            
            # Update transmit status text
            if int(sgant_transmit) == 0:
                self._set_text(self.ids.sgant_transmit, 'text', "RESET")
            elif int(sgant_transmit) == 1:
                self._set_text(self.ids.sgant_transmit, 'text', "NORMAL")
            else:
                self._set_text(self.ids.sgant_transmit, 'text', "n/a")
            
            # Update radio and TDRS based on transmit and AOS status
            if float(sgant_transmit) == 1.0 and float(aos) == 1.0:
                # Active transmission and AOS
                self._set_text(self.ids.radio_up, 'color', (1, 1, 1, 1))
                
                # Update TDRS sources based on station mode
                if hasattr(self, 'stationmode'):
                    if self.stationmode == "WEST":
                        self._set_text(self.ids.tdrs_west10, 'source', f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.zip")
                        self._set_text(self.ids.tdrs_west11, 'source', f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.png")
                        self._set_text(self.ids.tdrs_east12, 'source', f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.png")
                        self._set_text(self.ids.tdrs_east6, 'source', f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.png")
                        self._set_text(self.ids.tdrs_z7, 'source', f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.png")
                    elif self.stationmode == "EAST":
                        self._set_text(self.ids.tdrs_west11, 'source', f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.zip")
                        self._set_text(self.ids.tdrs_west10, 'source', f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.png")
                        self._set_text(self.ids.tdrs_east12, 'source', f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.zip")
                        self._set_text(self.ids.tdrs_east6, 'source', f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.png")
                        self._set_text(self.ids.tdrs_z7, 'source', f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.png")
                    elif self.stationmode == "ZENITH":
                        self._set_text(self.ids.tdrs_west11, 'source', f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.png")
                        self._set_text(self.ids.tdrs_west10, 'source', f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.png")
                        self._set_text(self.ids.tdrs_east6, 'source', f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.zip")
                        self._set_text(self.ids.tdrs_east12, 'source', f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.png")
                        self._set_text(self.ids.tdrs_z7, 'source', f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.zip")
            
            elif float(aos) == 0.0 and (float(sgant_transmit) == 0.0 or float(sgant_transmit) == 1.0):
                # No AOS, turn off radio and reset TDRS
                self._set_text(self.ids.radio_up, 'color', (0, 0, 0, 0))
                self._set_text(self.ids.tdrs_east12, 'source', f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.png")
                self._set_text(self.ids.tdrs_east6, 'source', f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.png")
                self._set_text(self.ids.tdrs_west11, 'source', f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.png")
                self._set_text(self.ids.tdrs_west10, 'source', f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.png")
                self._set_text(self.ids.tdrs_z7, 'source', f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.png")
            
            conn.close()
            
        except Exception as e:
            log_error(f"Error updating SGANT values: {e}")
    
    def _set_text(self, widget, property_name, value):
        """Helper method to safely set widget properties"""
        try:
            if hasattr(widget, property_name):
                setattr(widget, property_name, value)
        except Exception as e:
            log_error(f"Error setting {property_name} on {widget}: {e}")
