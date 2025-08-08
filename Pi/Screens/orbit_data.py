from __future__ import annotations

import pathlib
import json
import math
import sqlite3
from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.properties import StringProperty

from ._base import MimicBase
from utils.logger import log_info, log_error

kv_path = pathlib.Path(__file__).with_name("Orbit_Data.kv")
Builder.load_file(str(kv_path))

class Orbit_Data(MimicBase):
    """
    Orbit Data Screen - Displays detailed orbital mechanics and state vectors.
    Features:
    - Orbital elements (semi-major axis, eccentricity, inclination, etc.)
    - State vectors (position and velocity)
    - Real-time telemetry updates
    """

    mimic_directory = StringProperty(
        str(pathlib.Path(__file__).resolve().parents[3])   # /home/pi/Mimic
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.last_update_time = 0

    def on_enter(self):
        """Called when the orbit data screen is entered."""
        log_info("Orbit Data Screen Initialized")
        
        # Start periodic updates
        Clock.schedule_interval(self.update_orbit_data, 1)

    def on_leave(self):
        """Called when leaving the orbit data screen."""
        log_info("Orbit Data Screen Leaving - Cleaning up scheduled events")
        Clock.unschedule(self.update_orbit_data)

    def get_telemetry_data(self) -> tuple[list, list]:
        """Get telemetry data from the database."""
        try:
            # Database path - cross-platform handling
            db_path = pathlib.Path("/dev/shm/iss_telemetry.db")
            if not db_path.exists():
                db_path = pathlib.Path.home() / ".mimic_data" / "iss_telemetry.db"
                if not db_path.exists():
                    log_error("Telemetry database not found")
                    return [], []
            
            conn = sqlite3.connect(str(db_path))
            c = conn.cursor()
            
            c.execute('select Value from telemetry')
            values = c.fetchall()
            c.execute('select Timestamp from telemetry')
            timestamps = c.fetchall()
            
            conn.close()
            return values, timestamps
            
        except Exception as exc:
            log_error(f"Get telemetry data failed: {exc}")
            return [], []

    def calculate_orbital_elements(self, pos_vec: list, vel_vec: list) -> dict:
        """Calculate orbital elements from state vectors."""
        try:
            # Helper functions
            def dot(a, b):
                return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]
            
            def cross(a, b):
                return [a[1]*b[2] - a[2]*b[1],
                       a[2]*b[0] - a[0]*b[2],
                       a[0]*b[1] - a[1]*b[0]]
            
            def safe_divide(numerator, denominator):
                return numerator / denominator if denominator != 0 else 0
            
            # Earth's gravitational parameter (km³/s²)
            mu = 398600.4418
            
            # Calculate position and velocity magnitudes
            pos_mag = math.sqrt(dot(pos_vec, pos_vec))
            vel_mag = math.sqrt(dot(vel_vec, vel_vec))
            
            # Calculate specific angular momentum vector
            h_vec = cross(pos_vec, vel_vec)
            h_mag = math.sqrt(dot(h_vec, h_vec))
            
            # Calculate inclination
            inc = math.acos(safe_divide(h_vec[2], h_mag))
            
            # Calculate Right Ascension of Ascending Node (RAAN)
            node_vec = cross([0, 0, 1], h_vec)
            node_mag = math.sqrt(dot(node_vec, node_vec))
            
            raan = math.acos(safe_divide(node_vec[0], node_mag))
            if node_vec[1] < 0:
                raan = math.radians(360) - raan
            
            # Calculate eccentricity vector
            v_radial = safe_divide(dot(vel_vec, pos_vec), pos_mag)
            
            # e = (v² - μ/r)r - (r·v)v / μ
            pvnew = [x * (math.pow(vel_mag, 2) - (mu/pos_mag)) for x in pos_vec]
            vvnew = [x * (pos_mag * v_radial) for x in vel_vec]
            e_vec1 = [(1/mu) * x for x in pvnew]
            e_vec2 = [(1/mu) * x for x in vvnew]
            e_vec = [e_vec1[0] - e_vec2[0], e_vec1[1] - e_vec2[1], e_vec1[2] - e_vec2[2]]
            e_mag = math.sqrt(dot(e_vec, e_vec))
            
            # Calculate argument of periapsis
            arg_per = math.acos(safe_divide(dot(node_vec, e_vec), (node_mag * e_mag)))
            if e_vec[2] <= 0:
                arg_per = math.radians(360) - arg_per
            
            # Calculate true anomaly
            ta = math.acos(safe_divide(dot(e_vec, pos_vec), (e_mag * pos_mag)))
            if v_radial <= 0:
                ta = math.radians(360) - ta
            
            # Calculate apogee and perigee
            apogee = (math.pow(h_mag, 2) / mu) * (safe_divide(1, (1 + e_mag * math.cos(math.radians(180)))))
            perigee = (math.pow(h_mag, 2) / mu) * (safe_divide(1, (1 + e_mag * math.cos(0))))
            apogee_height = apogee - 6371.00  # Earth radius
            perigee_height = perigee - 6371.00
            
            # Calculate semi-major axis
            sma = 0.5 * (apogee + perigee)  # km
            
            # Calculate orbital period
            if sma >= 0:
                period = ((safe_divide(2 * math.pi, math.sqrt(mu))) * math.pow(sma, 3/2)) / 60  # minutes
            else:
                period = 0
            
            return {
                'inc': inc,
                'raan': raan,
                'e_mag': e_mag,
                'arg_per': arg_per,
                'ta': ta,
                'apogee_height': apogee_height,
                'perigee_height': perigee_height,
                'sma': sma,
                'period': period
            }
            
        except Exception as exc:
            log_error(f"Calculate orbital elements failed: {exc}")
            return {
                'inc': 0, 'raan': 0, 'e_mag': 0, 'arg_per': 0, 'ta': 0,
                'apogee_height': 0, 'perigee_height': 0, 'sma': 0, 'period': 0
            }

    def update_orbit_data(self, _dt=0):
        """Update all orbit data displays with current telemetry."""
        try:
            # Get telemetry data from database
            values, timestamps = self.get_telemetry_data()

            if not values or len(values) < 61:
                log_error("Insufficient telemetry data for orbit calculations")
                return
            
            # Extract ISS state vectors (indices 55-60 from GUI.py)
            position_x = float(values[55][0])  # km
            position_y = float(values[56][0])  # km
            position_z = float(values[57][0])  # km
            velocity_x = float(values[58][0]) / 1000.0  # convert to km/s
            velocity_y = float(values[59][0]) / 1000.0  # convert to km/s
            velocity_z = float(values[60][0]) / 1000.0  # convert to km/s
            
            # Create position and velocity vectors
            pos_vec = [position_x, position_y, position_z]
            vel_vec = [velocity_x, velocity_y, velocity_z]
            
            # Calculate orbital elements
            orbital_elements = self.calculate_orbital_elements(pos_vec, vel_vec)
            
            # Update UI elements with calculated values
            if 'inc' in self.ids:
                self.ids.inc.text = f"{math.degrees(orbital_elements['inc']):.2f}"
            if 'raan' in self.ids:
                self.ids.raan.text = f"{math.degrees(orbital_elements['raan']):.2f}"
            if 'e' in self.ids:
                self.ids.e.text = f"{orbital_elements['e_mag']:.4f}"
            if 'arg_per' in self.ids:
                self.ids.arg_per.text = f"{math.degrees(orbital_elements['arg_per']):.2f}"
            if 'true_anomaly' in self.ids:
                self.ids.true_anomaly.text = f"{math.degrees(orbital_elements['ta']):.2f}"
            if 'apogee_height' in self.ids:
                self.ids.apogee_height.text = f"{orbital_elements['apogee_height']:.2f}"
            if 'perigee_height' in self.ids:
                self.ids.perigee_height.text = f"{orbital_elements['perigee_height']:.2f}"
            if 'sma' in self.ids:
                self.ids.sma.text = f"{orbital_elements['sma']:.2f}"
            
            # Update state vectors
            if 'position_x' in self.ids:
                self.ids.position_x.text = f"{position_x:.2f}"
            if 'position_y' in self.ids:
                self.ids.position_y.text = f"{position_y:.2f}"
            if 'position_z' in self.ids:
                self.ids.position_z.text = f"{position_z:.2f}"
            if 'velocity_x' in self.ids:
                self.ids.velocity_x.text = f"{velocity_x:.2f}"
            if 'velocity_y' in self.ids:
                self.ids.velocity_y.text = f"{velocity_y:.2f}"
            if 'velocity_z' in self.ids:
                self.ids.velocity_z.text = f"{velocity_z:.2f}"
                
        except Exception as exc:
            log_error(f"Update orbit data failed: {exc}")
            import traceback
            traceback.print_exc()
