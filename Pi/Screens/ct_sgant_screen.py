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
import math

kv_path = pathlib.Path(__file__).with_name("CT_SGANT_Screen.kv")
Builder.load_file(str(kv_path))

class CT_SGANT_Screen(MimicBase):
    _update_event = None
    
    def on_enter(self):
        """Called when the screen is entered - start updating values"""
        try:
            self.update_sgant_values(0)
            self._update_event = Clock.schedule_interval(self.update_sgant_values, 2.0)
            log_info("CT_SGANT: started updates (2s)")
        except Exception as exc:
            log_error(f"CT_SGANT on_enter failed: {exc}")
    
    def on_leave(self):
        """Called when the screen is left - stop updating values"""
        try:
            if self._update_event:
                self._update_event.cancel()
                self._update_event = None
            log_info("CT_SGANT: stopped updates")
        except Exception as exc:
            log_error(f"CT_SGANT on_leave failed: {exc}")
    
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
            
            # Get ISS position for longitude calculation
            position_x = float(values[57][0]) if values[57][0] else 0.0
            position_y = float(values[58][0]) if values[58][0] else 0.0
            position_z = float(values[59][0]) if values[59][0] else 0.0
            
            # Calculate ISS longitude from position vector
            if position_x != 0 or position_y != 0:
                lon_rad = math.atan2(position_y, position_x)
                iss_longitude = math.degrees(lon_rad)
            else:
                iss_longitude = 0.0
            
            # Update SGANT dish angle - convert elevation to rotation angle
            if 'sgant_dish' in self.ids:
                self.ids.sgant_dish.angle = sgant_elevation
            
            # Update elevation display
            if 'sgant_elevation' in self.ids:
                self.ids.sgant_elevation.text = f"{sgant_elevation:.2f}"
                print(f"SGANT elevation: {sgant_elevation}")
            else:
                print("sgant_elevation not found")
            
            # Update transmit status text
            if 'sgant_transmit' in self.ids:
                print(f"SGANT transmit: {sgant_transmit}")
                if int(sgant_transmit) == 0:
                    self.ids.sgant_transmit.text = "RESET"
                elif int(sgant_transmit) == 1:
                    self.ids.sgant_transmit.text = "NORMAL"
                else:
                    self.ids.sgant_transmit.text = "n/a"
            else:
                print("sgant_transmit not found")
            
            # Update radio and TDRS based on transmit and AOS status
            if float(sgant_transmit) == 1.0 and float(aos) == 1.0:
                # Active transmission and AOS
                if 'radio_up' in self.ids:
                    self.ids.radio_up.color = (1, 1, 1, 1)
                
                # Update TDRS sources based on station mode
                # For now, use a default mode since stationmode is not defined
                active_tdrs_group = "WEST"  # Default mode
                
                if active_tdrs_group == "WEST":
                    if 'tdrs_west10' in self.ids:
                        self.ids.tdrs_west10.source = f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.zip"
                    if 'tdrs_west11' in self.ids:
                        self.ids.tdrs_west11.source = f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.zip"
                    if 'tdrs_east12' in self.ids:
                        self.ids.tdrs_east12.source = f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.png"
                    if 'tdrs_east6' in self.ids:
                        self.ids.tdrs_east6.source = f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.png"
                    if 'tdrs_z7' in self.ids:
                        self.ids.tdrs_z7.source = f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.png"
                    if 'tdrs_z8' in self.ids:
                        self.ids.tdrs_z8.source = f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.png"
                elif active_tdrs_group == "EAST":
                    if 'tdrs_west11' in self.ids:
                        self.ids.tdrs_west11.source = f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.png"
                    if 'tdrs_west10' in self.ids:
                        self.ids.tdrs_west10.source = f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.png"
                    if 'tdrs_east12' in self.ids:
                        self.ids.tdrs_east12.source = f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.zip"
                    if 'tdrs_east6' in self.ids:
                        self.ids.tdrs_east6.source = f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.zip"
                    if 'tdrs_z7' in self.ids:
                        self.ids.tdrs_z7.source = f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.png"
                    if 'tdrs_z8' in self.ids:
                        self.ids.tdrs_z8.source = f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.png"
                elif active_tdrs_group == "Z":
                    if 'tdrs_west11' in self.ids:
                        self.ids.tdrs_west11.source = f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.png"
                    if 'tdrs_west10' in self.ids:
                        self.ids.tdrs_west10.source = f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.png"
                    if 'tdrs_east6' in self.ids:
                        self.ids.tdrs_east6.source = f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.png"
                    if 'tdrs_east12' in self.ids:
                        self.ids.tdrs_east12.source = f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.png"
                    if 'tdrs_z7' in self.ids:
                        self.ids.tdrs_z7.source = f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.zip"
                    if 'tdrs_z8' in self.ids:
                        self.ids.tdrs_z8.source = f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.zip"
            
            elif float(aos) == 0.0 and (float(sgant_transmit) == 0.0 or float(sgant_transmit) == 1.0):
                # No AOS, turn off radio and reset TDRS
                if 'radio_up' in self.ids:
                    self.ids.radio_up.color = (0, 0, 0, 0)
                if 'tdrs_east12' in self.ids:
                    self.ids.tdrs_east12.source = f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.png"
                if 'tdrs_east6' in self.ids:
                    self.ids.tdrs_east6.source = f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.png"
                if 'tdrs_west11' in self.ids:
                    self.ids.tdrs_west11.source = f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.png"
                if 'tdrs_west10' in self.ids:
                    self.ids.tdrs_west10.source = f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.png"
                if 'tdrs_z7' in self.ids:
                    self.ids.tdrs_z7.source = f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.png"
                if 'tdrs_z8' in self.ids:
                    self.ids.tdrs_z8.source = f"{self.mimic_directory}/Mimic/Pi/imgs/ct/TDRS.png"
            
            conn.close()
            
            # Update TDRS widget positions based on ISS longitude
            self.update_tdrs_positions(iss_longitude)
            
            # Update TDRS label with active satellite info
            self.update_tdrs_label()
            
        except Exception as e:
            log_error(f"Error updating SGANT values: {e}")
    
    def update_tdrs_positions(self, iss_longitude):
        """Update TDRS widget positions based on ISS longitude"""
        try:
            # Position TDRS widgets using the hardcoded adjustment values from user
            if 'tdrs_east12' in self.ids:
                self.ids.tdrs_east12.angle = (-1 * iss_longitude) - 41
            if 'tdrs_east6' in self.ids:
                self.ids.tdrs_east6.angle = (-1 * iss_longitude) - 46
            if 'tdrs_z7' in self.ids:
                self.ids.tdrs_z7.angle = ((-1 * iss_longitude) - 41) + 126
            if 'tdrs_z8' in self.ids:
                self.ids.tdrs_z8.angle = ((-1 * iss_longitude) - 41) + 127
            if 'tdrs_west11' in self.ids:
                self.ids.tdrs_west11.angle = ((-1 * iss_longitude) - 41) - 133
            if 'tdrs_west10' in self.ids:
                self.ids.tdrs_west10.angle = ((-1 * iss_longitude) - 41) - 130
                
            log_info(f"Updated TDRS positions with ISS longitude: {iss_longitude:.2f}°")
            
        except Exception as e:
            log_error(f"Error updating TDRS positions: {e}")
    
    def update_tdrs_label(self):
        """Update the TDRS label with active satellite information"""
        try:
            # Try to read from TDRS database
            tdrs_db_path = Path("/dev/shm/tdrs.db")
            if not tdrs_db_path.exists():
                # Try Windows path
                tdrs_db_path = Path.home() / ".mimic_data" / "tdrs.db"
                if not tdrs_db_path.exists():
                    if 'tdrs_label' in self.ids:
                        self.ids.tdrs_label.text = 'TDRS: No Database'
                    return
            
            conn = sqlite3.connect(str(tdrs_db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT TDRS1, TDRS2 FROM tdrs LIMIT 1")
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0] and result[1]:
                active_tdrs = []
                if result[0] != '0':
                    active_tdrs.append(f"TDRS {result[0]} Connected")
                if result[1] != '0':
                    active_tdrs.append(f"TDRS {result[1]} Connected")
                
                if active_tdrs:
                    if 'tdrs_label' in self.ids:
                        self.ids.tdrs_label.text = f"Active: {', '.join(active_tdrs)}"
                else:
                    if 'tdrs_label' in self.ids:
                        self.ids.tdrs_label.text = 'TDRS: No Active Connections'
            else:
                if 'tdrs_label' in self.ids:
                    self.ids.tdrs_label.text = 'TDRS: No Active Satellites'
                
        except Exception as e:
            log_error(f"Error updating TDRS label: {e}")
            if 'tdrs_label' in self.ids:
                self.ids.tdrs_label.text = 'TDRS: Error'
    
    def _set_text(self, widget, property_name, value):
        """Helper method to safely set widget properties"""
        try:
            if hasattr(widget, property_name):
                setattr(widget, property_name, value)
        except Exception as e:
            log_error(f"Error setting {property_name} on {widget}: {e}")
