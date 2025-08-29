from __future__ import annotations
from kivy.uix.screenmanager import Screen
import pathlib
from kivy.properties import StringProperty
from kivy.lang import Builder
from kivy.clock import Clock
from ._base import MimicBase
from utils.logger import log_info, log_error
from utils.serial import serialWrite
import sqlite3
from datetime import datetime
import math

kv_path = pathlib.Path(__file__).with_name("ISS_Screen.kv")
Builder.load_file(str(kv_path))

class ISS_Screen(MimicBase):
    """
    Shows station layout; user taps a module to highlight it.
    `selected_module` is kept both on the Screen instance *and*
    mirrored up to `App.get_running_app().current_module`
    so other screens can read it - cleaner than a global variable
    """

    selected_module = StringProperty("")
    
    # Telemetry update interval (seconds)
    TELEMETRY_UPDATE_INTERVAL = 1.0
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._telemetry_event = None
        
    def on_enter(self):
        log_info("ISS Screen: on_enter")
        """Called when the screen is entered."""
        super().on_enter()
        # Start telemetry updates
        self._start_telemetry_updates()
        
    def on_leave(self):
        """Called when the screen is left."""
        super().on_leave()
        # Stop telemetry updates
        self._stop_telemetry_updates()
        
    def _start_telemetry_updates(self):
        """Start periodic telemetry updates."""
        if self._telemetry_event is None:
            self._telemetry_event = Clock.schedule_interval(
                self._update_telemetry_values, 
                self.TELEMETRY_UPDATE_INTERVAL
            )
            log_info("ISS Screen: Started telemetry updates")
            
    def _stop_telemetry_updates(self):
        """Stop periodic telemetry updates."""
        if self._telemetry_event is not None:
            self._telemetry_event.cancel()
            self._telemetry_event = None
            log_info("ISS Screen: Stopped telemetry updates")
            
    def _get_db_path(self) -> pathlib.Path:
        """Get database path with cross-platform handling."""
        shm = pathlib.Path('/dev/shm/iss_telemetry.db')
        if shm.exists():
            return shm
        return pathlib.Path.home() / '.mimic_data' / 'iss_telemetry.db'
            
    def _update_telemetry_values(self, dt):
        """Update ISS telemetry values from database."""
        try:
            # Get database path
            db_path = self._get_db_path()
            if not db_path.exists():
                log_error("ISS Screen: Telemetry database not found")
                return
                
            # Connect to database
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Get telemetry values
            cursor.execute('SELECT Value FROM telemetry')
            values = cursor.fetchall()
            
            if not values or len(values) < 61:  # Ensure we have enough values including state vectors
                log_error("ISS Screen: Insufficient telemetry data")
                conn.close()
                return
                
            # Update station mode
            self._update_station_mode(values)
            
            # Update ISS telemetry values including altitude and velocity
            self._update_iss_telemetry(values)
            
            conn.close()
            
        except Exception as e:
            log_error(f"ISS Screen: Error updating telemetry: {e}")
            
    def _update_station_mode(self, values):
        """Update station mode display based on telemetry."""
        try:
            stationmode = float(values[46][0])  # Russian segment mode same as USOS mode
            
            if stationmode == 1.0:
                self.ids.stationmode_value.text = "Crew Rescue"
            elif stationmode == 2.0:
                self.ids.stationmode_value.text = "Survival"
            elif stationmode == 3.0:
                self.ids.stationmode_value.text = "Reboost"
            elif stationmode == 4.0:
                self.ids.stationmode_value.text = "Proximity Operations"
            elif stationmode == 5.0:
                self.ids.stationmode_value.text = "EVA"
            elif stationmode == 6.0:
                self.ids.stationmode_value.text = "Microgravity"
            elif stationmode == 7.0:
                self.ids.stationmode_value.text = "Standard"
            else:
                self.ids.stationmode_value.text = "n/a"
                
        except (IndexError, ValueError, TypeError) as e:
            log_error(f"ISS Screen: Error updating station mode: {e}")
            self.ids.stationmode_value.text = "n/a"
            
    def _update_iss_telemetry(self, values):
        """Update ISS altitude, velocity, and mass values from state vectors."""
        try:
            # Get ISS mass from telemetry
            iss_mass = float(values[48][0])  # iss_mass at index 48
            self.ids.stationmass_value.text = f"{iss_mass:.2f} kg"
            
            # Calculate altitude and velocity from state vectors
            # State vectors are at indices 55-60
            position_x = float(values[55][0])  # km
            position_y = float(values[56][0])  # km
            position_z = float(values[57][0])  # km
            velocity_x = float(values[58][0]) / 1000.0  # convert to km/s
            velocity_y = float(values[59][0]) / 1000.0  # convert to km/s
            velocity_z = float(values[60][0]) / 1000.0  # convert to km/s
            
            # Calculate altitude (distance from Earth center minus Earth radius)
            # Earth radius is approximately 6371 km
            altitude = math.sqrt(position_x**2 + position_y**2 + position_z**2) - 6371.0
            
            # Calculate velocity magnitude
            velocity = math.sqrt(velocity_x**2 + velocity_y**2 + velocity_z**2)
            
            # Update altitude and velocity displays
            self.ids.altitude_value.text = f"{altitude:.2f} km"
            self.ids.velocity_value.text = f"{velocity:.2f} km/s"
            
        except (IndexError, ValueError, TypeError) as e:
            log_error(f"ISS Screen: Error updating ISS telemetry: {e}")
            self.ids.stationmass_value.text = "n/a"
            self.ids.altitude_value.text = "n/a"
            self.ids.velocity_value.text = "n/a"
            
    def update_altitude_velocity(self, altitude: float, velocity: float):
        """Update altitude and velocity values (for external updates)."""
        try:
            self.ids.altitude_value.text = f"{altitude:.2f} km"
            self.ids.velocity_value.text = f"{velocity:.2f} km/s"
        except Exception as e:
            log_error(f"ISS Screen: Error updating altitude/velocity: {e}")
            
    def get_station_mode(self) -> str:
        """Get current station mode text."""
        return self.ids.stationmode_value.text
        
    def get_iss_mass(self) -> str:
        """Get current ISS mass text."""
        return self.ids.stationmass_value.text
        
    def get_altitude(self) -> str:
        """Get current altitude text."""
        return self.ids.altitude_value.text
        
    def get_velocity(self) -> str:
        """Get current velocity text."""
        return self.ids.velocity_value.text

    # ------------------------------------------------------------------
    # bound in KV:  on_press: root.select_module("US LAB")
    # ------------------------------------------------------------------

    def select_module(self, mod_name: str) -> None:
        """Select a module and update the display."""
        self.selected_module = mod_name
        
        log_info(f"ISS Screen: selected -> {mod_name}")

        # Serial write the module name to the arduino
        serialWrite(f"ISS={mod_name}")
        
        # Update the module stack image based on selection
        if mod_name == "reset":
            # Reset to default image
            self.ids.modulestack.source = f"{self.mimic_directory}/Mimic/Pi/imgs/iss/LEDstack2.png"
        else:
            # Update to selected module image
            module_image_map = {
                "SM": "LEDstack2_SM.png",
                "FGB": "LEDstack2_FGB.png", 
                "Node1": "LEDstack2_Node1.png",
                "AL": "LEDstack2_AL.png",
                "Node3": "LEDstack2_Node3.png",
                "PMM": "LEDstack2_PMM.png",
                "BEAM": "LEDstack2_BEAM.png",
                "USL": "LEDstack2_USL.png",
                "Node2": "LEDstack2_Node2.png",
                "Col": "LEDstack2_Col.png",
                "JLP": "LEDstack2_JLP.png",
                "JEM": "LEDstack2_JEM.png",
                "NRAL": "LEDstack2_NRAL.png"
            }
            
            if mod_name in module_image_map:
                self.ids.modulestack.source = f"{self.mimic_directory}/Mimic/Pi/imgs/iss/{module_image_map[mod_name]}"

