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
import json
import ephem
from datetime import datetime

kv_path = pathlib.Path(__file__).with_name("CT_SGANT_Screen.kv")
Builder.load_file(str(kv_path))

class CT_SGANT_Screen(MimicBase):
    _update_event = None
    tdrs_tles = {}  # Store TDRS TLE data
    
    def on_enter(self):
        """Called when the screen is entered - start updating values"""
        try:
            self.load_tdrs_tles()
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
    
    def load_tdrs_tles(self):
        """Load TDRS TLE data from configuration file"""
        try:
            cfg = Path.home() / ".mimic_data" / "tdrs_tle_config.json"
            if cfg.exists():
                db = json.loads(cfg.read_text())
                # Load only the TDRS satellites we need
                tdrs_ids = {"TDRS 6", "TDRS 12", "TDRS 7", "TDRS 8", "TDRS 10", "TDRS 11"}
                self.tdrs_tles = {
                    name: ephem.readtle(name, *lines)
                    for name, lines in db["TDRS_TLEs"].items()
                    if name in tdrs_ids
                }
                log_info(f"Loaded {len(self.tdrs_tles)} TDRS TLEs")
            else:
                log_error("TDRS TLE config file not found")
        except Exception as exc:
            log_error(f"Failed to load TDRS TLEs: {exc}")
    
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
                return
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute('select Value from telemetry')
            values = cur.fetchall()
            
            # Extract SGANT values using indices from database_initialize.py
            sgant_elevation = float((values[15])[0])
            sgant_xelevation = float((values[17])[0])
            sgant_transmit = float((values[41])[0])
            aos = float((values[12])[0])
            
            # Get ISS position for longitude calculation
            position_x = float((values[57])[0])
            position_y = float((values[58])[0])
            position_z = float((values[59])[0])
            
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
            else:
                log_error("sgant_elevation not found")
            
            # Update transmit status text
            if 'sgant_transmit' in self.ids:
                if int(sgant_transmit) == 0:
                    self.ids.sgant_transmit.text = "RESET"
                elif int(sgant_transmit) == 1:
                    self.ids.sgant_transmit.text = "NORMAL"
                else:
                    self.ids.sgant_transmit.text = "n/a"
            else:
                log_error("sgant_transmit not found")
            
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
            
            # Update TDRS widget positions based on actual orbital positions
            self.update_tdrs_positions(iss_longitude)
            
            # Update TDRS label with active satellite info
            self.update_tdrs_label()
            
        except Exception as e:
            log_error(f"Error updating SGANT values: {e}")
    
    def update_tdrs_positions(self, iss_longitude):
        """Update TDRS widget positions based on their actual orbital positions relative to ISS"""
        try:
            if not self.tdrs_tles:
                log_error("No TDRS TLE data available")
                return
            
            # Get active TDRS from database
            active_tdrs = self.get_active_tdrs()
            
            # Calculate positions for each TDRS based on their actual orbital longitude
            for name, sat in self.tdrs_tles.items():
                try:
                    # Compute current TDRS position
                    sat.compute(datetime.utcnow())
                    tdrs_longitude = math.degrees(sat.sublong)
                    
                    # Calculate relative longitude difference (how far TDRS is from ISS)
                    # Normalize to -180 to +180 range
                    relative_lon = tdrs_longitude - iss_longitude
                    while relative_lon > 180:
                        relative_lon -= 360
                    while relative_lon < -180:
                        relative_lon += 360
                    
                    # Convert relative longitude to rotation angle around the SGANT dish
                    # 0° = top of screen, 90° = right, 180° = bottom, 270° = left
                    rotation_angle = relative_lon
                    
                    # Map to the correct widget ID
                    widget_id = self.get_tdrs_widget_id(name)
                    if widget_id and widget_id in self.ids:
                        self.ids[widget_id].angle = rotation_angle
                        print(f"Updated {widget_id} angle to {rotation_angle}")
                        # Only show TDRS images for active satellites
                        if self.is_tdrs_active(name, active_tdrs):
                            self.ids[widget_id].opacity = 1.0
                            print(f"Updated {widget_id} opacity to 1.0")
                        else:
                            self.ids[widget_id].opacity = 0.3
                            print(f"Updated {widget_id} opacity to 0.3")
                    
                except Exception as exc:
                    log_error(f"Failed to calculate position for {name}: {exc}")
                    continue
            
        except Exception as e:
            log_error(f"Error updating TDRS positions: {e}")
    
    def get_tdrs_widget_id(self, tdrs_name):
        """Map TDRS name to widget ID"""
        mapping = {
            "TDRS 6": "tdrs_east6",
            "TDRS 12": "tdrs_east12", 
            "TDRS 7": "tdrs_z7",
            "TDRS 8": "tdrs_z8",
            "TDRS 10": "tdrs_west10",
            "TDRS 11": "tdrs_west11"
        }
        return mapping.get(tdrs_name)
    
    def get_active_tdrs(self):
        """Get list of active TDRS numbers from database"""
        try:
            tdrs_db_path = Path("/dev/shm/tdrs.db")
            if not tdrs_db_path.exists():
                tdrs_db_path = Path.home() / ".mimic_data" / "tdrs.db"
                if not tdrs_db_path.exists():
                    return []
            
            conn = sqlite3.connect(str(tdrs_db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT TDRS1, TDRS2 FROM tdrs LIMIT 1")
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0] and result[1]:
                active_tdrs = []
                if result[0] != '0':
                    active_tdrs.append(int(result[0]))
                if result[1] != '0':
                    active_tdrs.append(int(result[1]))
                return active_tdrs
            return []
            
        except Exception as e:
            log_error(f"Error getting active TDRS: {e}")
            return []
    
    def is_tdrs_active(self, tdrs_name, active_tdrs):
        """Check if a TDRS is currently active"""
        try:
            # Extract TDRS number from name (e.g., "TDRS 6" -> 6)
            tdrs_number = int(tdrs_name.split()[1])
            return tdrs_number in active_tdrs
        except:
            return False
    
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
