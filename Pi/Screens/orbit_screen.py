# Pi/Screens/orbit_screen.py
from __future__ import annotations

import json, math, pytz, sqlite3, time
from pathlib import Path
from subprocess import Popen
from typing import Optional
from kivy.base import ExceptionManager, ExceptionHandler
import traceback, sys, logging

class _Reraise(ExceptionHandler):
    def handle_exception(self, inst):
        traceback.print_exception(type(inst), inst, inst.__traceback__, file=sys.stderr)
        logging.getLogger("Mimic").exception("Unhandled Kivy error")
        return ExceptionManager.PASS

ExceptionManager.add_handler(_Reraise())

from math import degrees
from datetime import datetime, timedelta
import ephem
from kivy.clock import Clock
from kivy.lang import Builder

from ._base import MimicBase
from utils.logger import log_info, log_error

Builder.load_file(str(Path(__file__).with_name("Orbit_Screen.kv")))

# ────────────────────────────────────────────────────────────────────────────
class Orbit_Screen(MimicBase):
    """Everything related to ground tracks, TDRS icons, next-pass timers."""
    """
    Everything related to ground tracks, TDRS icons, next-pass timers.
    Only six satellites are shown:
        • East  : TDRS 6, 12
        • Z-belt: TDRS 7, 8
        • West  : TDRS 10, 11
    """

    _TDRS_IDS = {"TDRS 6", "TDRS 12", "TDRS 7", "TDRS 8", "TDRS 10", "TDRS 11"}

    # ---------------------------------------------------------------- state
    iss_tle:          Optional[ephem.EarthSatellite] = None
    tdrs_tles:        dict[str, ephem.EarthSatellite] = {}
    location         = ephem.Observer()          # reused by many helpers
    last_map_refresh = 0.                        # epoch seconds
    
    # User location (default: Houston, TX)
    user_lat: float = 29.585736
    user_lon: float = -95.1327829
    
    # Active TDRS tracking
    active_tdrs: list[int] = [0, 0]  # TDRS1, TDRS2 from database
    
    # Orbit counting
    last_daily_reset: datetime = None  # Track when we last reset daily counter
    
    # ZOE calculation caching
    _zoe_boundary_cache: Optional[list] = None
    _zoe_cache_time: float = 0.0
    _zoe_cache_duration: float = 3600.0  # Cache for 1 hour (ZOE is very stable)

    # ---------------------------------------------------------------- enter
    def on_enter(self):
        log_info("Orbit Screen Initialized")
        
        
        # periodic updates
        Clock.schedule_interval(self.update_orbit,         1)
        Clock.schedule_interval(self.update_iss,           1)
        Clock.schedule_interval(self.update_groundtrack,   1)
        Clock.schedule_interval(self.update_nightshade,  120)
        Clock.schedule_interval(self.update_orbit_map,    31)
        Clock.schedule_interval(self.update_globe_image,  55)
        Clock.schedule_interval(self.update_globe,        31)
        Clock.schedule_interval(self.update_tdrs,        607)
        Clock.schedule_interval(self.update_sun,         489) 

        # one-shots that existed in MainApp.build()
        Clock.schedule_once(self.update_iss_tle,          60)
        Clock.schedule_once(self.update_tdrs_tle,          7)
        Clock.schedule_once(self.update_tdrs,              5)
        Clock.schedule_once(self.update_nightshade,       15)
        Clock.schedule_once(self.update_sun,              11)
        
        # Update user location on screen enter
        Clock.schedule_once(self.update_user_location,     1)
        
        # Update active TDRS circles
        Clock.schedule_interval(self.update_active_tdrs,   2)  # Check every 2 seconds
        Clock.schedule_once(self.update_active_tdrs,       5)  # Initial check after 5 seconds

    # ---------------------------------------------------------------- leave
    def on_leave(self):
        log_info("Orbit Screen Leaving - Cleaning up scheduled events")
        # Cancel all scheduled events to prevent memory leaks and unnecessary processing
        Clock.unschedule(self.update_orbit)
        Clock.unschedule(self.update_iss)
        Clock.unschedule(self.update_groundtrack)
        Clock.unschedule(self.update_nightshade)
        Clock.unschedule(self.update_orbit_map)
        Clock.unschedule(self.update_globe_image)
        Clock.unschedule(self.update_globe)
        Clock.unschedule(self.update_tdrs)
        Clock.unschedule(self.update_sun)
        Clock.unschedule(self.update_active_tdrs) 

    # ─────────────────────── user location ─────────────────────────────────────
    def update_user_location(self, _dt=0) -> None:
        """Update the user location dot on the map."""
        try:
            if "user_location" not in self.ids:
                log_error("User location widget not found in KV file")
                return
                
            x, y = self.map_px(self.user_lat, self.user_lon)
            self.ids.user_location.center = (x, y)
            
        except Exception as exc:
            log_error(f"Update user location failed: {exc}")
            import traceback
            traceback.print_exc()

    def update_active_tdrs(self, _dt=0) -> None:
        """Update the active TDRS circles based on database."""
        try:
            # Read active TDRS from database
            tdrs_db_path = Path("/dev/shm/tdrs.db")
            if not tdrs_db_path.exists():
                # Try Windows path
                tdrs_db_path = Path.home() / ".mimic_data" / "tdrs.db"
                if not tdrs_db_path.exists():
                    log_error("TDRS database not found")
                    return
                
            conn = sqlite3.connect(str(tdrs_db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT TDRS1, TDRS2 FROM tdrs LIMIT 1")
            result = cursor.fetchone()
            conn.close()
            
            if result:
                new_active_tdrs = [int(result[0]) if result[0] != '0' else 0, 
                                  int(result[1]) if result[1] != '0' else 0]
                
                # Only update if the active TDRS have changed
                if new_active_tdrs != self.active_tdrs:
                    self.active_tdrs = new_active_tdrs
                    log_info(f"Active TDRS updated: {self.active_tdrs}")
                    
                    # Update all TDRS circle visibility
                    self._update_tdrs_circles()
                    
        except Exception as exc:
            log_error(f"Update active TDRS failed: {exc}")
            import traceback
            traceback.print_exc()

    def _update_tdrs_circles(self) -> None:
        """Update the visibility of active TDRS circles."""
        try:
            # TDRS IDs that can be active
            tdrs_ids = [6, 7, 8, 10, 11, 12]
            
            for tdrs_id in tdrs_ids:
                circle_id = f"TDRS{tdrs_id}_active_circle"
                
                if circle_id in self.ids:
                    circle_widget = self.ids[circle_id]
                    
                    # Show circle if this TDRS is active
                    if tdrs_id in self.active_tdrs:
                        circle_widget.opacity = 1.0
                        # Position the circle around the TDRS dot
                        tdrs_widget = self.ids[f"TDRS{tdrs_id}"]
                        circle_widget.center = tdrs_widget.center
                    else:
                        circle_widget.opacity = 0.0
                        
        except Exception as exc:
            log_error(f"Update TDRS circles failed: {exc}")
            import traceback
            traceback.print_exc()

    def _update_tdrs_labels(self) -> None:
        """Position TDRS group labels dynamically based on satellite positions."""
        try:
            # TDRS groups: East (6,12), Z-Belt (7,8), West (10,11)
            tdrs_groups = {
                'east': [6, 12],
                'zbelt': [7, 8], 
                'west': [10, 11]
            }
            
            for group_name, tdrs_ids in tdrs_groups.items():
                # Find the first visible TDRS in this group to position the label
                label_id = f"tdrs_{group_name}_label"
                if label_id not in self.ids:
                    continue
                    
                label_widget = self.ids[label_id]
                label_positioned = False
                group_active = False
                
                # Check if any TDRS in this group is active
                for tdrs_id in tdrs_ids:
                    if tdrs_id in self.active_tdrs:
                        group_active = True
                        break
                
                # Set label color based on group activity
                if group_active:
                    label_widget.color = (1, 0, 1, 1)  # Magenta when active
                else:
                    label_widget.color = (1, 1, 1, 1)  # White when inactive
                
                for tdrs_id in tdrs_ids:
                    tdrs_name = f"TDRS{tdrs_id}"
                    if tdrs_name in self.ids:
                        tdrs_widget = self.ids[tdrs_name]
                        # Position label near the TDRS dot with some offset
                        label_x = tdrs_widget.center_x + 0  # Offset right
                        label_y = tdrs_widget.center_y - 30  # Offset up
                        label_widget.pos = (label_x, label_y)
                        label_positioned = True
                        break
                
                # If no TDRS in group is visible, hide the label
                if not label_positioned:
                    label_widget.pos = (-1000, -1000)  # Move off-screen
                    
        except Exception as exc:
            log_error(f"Update TDRS labels failed: {exc}")
            import traceback
            traceback.print_exc()

    def calculate_total_orbits(self) -> int:
        """Calculate total lifetime orbits for ISS."""
        try:
            if not self.iss_tle:
                return 0
                
            # Get TLE epoch
            epoch = self.iss_tle.epoch
            epoch_dt = datetime.strptime(str(epoch), "%Y/%m/%d %H:%M:%S")
            
            # Calculate orbits since epoch
            now = datetime.utcnow()
            time_since_epoch = (now - epoch_dt).total_seconds()
            
            # ISS orbital period is approximately 92.5 minutes
            orbital_period_seconds = 92.5 * 60
            orbits_since_epoch = int(time_since_epoch / orbital_period_seconds)
            
            # Extract revolutions directly from TLE line 2 (characters 64-68)
            # We need to get the raw TLE data
            cfg = Path.home() / ".mimic_data" / "iss_tle_config.json"
            lines = json.loads(cfg.read_text())
            tle_line2 = lines["ISS_TLE_Line2"]
            
            # Extract revolutions (characters 64-68, 1-indexed)
            revolutions_str = tle_line2[63:68].strip()  # 0-indexed, so 63:68
            epoch_revolutions = int(revolutions_str)
            
            # Total = TLE revolutions + 100,000 + orbits since epoch
            total_orbits = epoch_revolutions + 100000 + orbits_since_epoch
            
            return total_orbits
            
        except Exception as exc:
            log_error(f"Calculate total orbits failed: {exc}")
            return 0

    def calculate_daily_orbits(self) -> int:
        """Calculate orbits completed today (since midnight in user's timezone)."""
        try:
            if not self.iss_tle:
                return 0
                
            # Get user's timezone (default to Houston)
            user_tz = pytz.timezone("America/Chicago")  # Houston timezone
            
            # Get current time in user's timezone
            now_utc = datetime.utcnow()
            now_local = now_utc.replace(tzinfo=pytz.utc).astimezone(user_tz)
            
            # Get midnight today in user's timezone
            midnight_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
            midnight_utc = midnight_local.astimezone(pytz.utc)
            
            # Calculate time since midnight (both times are now timezone-aware)
            time_since_midnight = (now_utc.replace(tzinfo=pytz.utc) - midnight_utc).total_seconds()
            
            # ISS orbital period is approximately 92.5 minutes
            orbital_period_seconds = 92.5 * 60
            daily_orbits = int(time_since_midnight / orbital_period_seconds)
            
            return daily_orbits
            
        except Exception as exc:
            log_error(f"Calculate daily orbits failed: {exc}")
            return 0

    def get_telemetry_data(self) -> tuple[list, list]:
        """Get telemetry data from the database."""
        try:
            import sqlite3
            from pathlib import Path
            
            # Database path - cross-platform handling
            db_path = Path("/dev/shm/iss_telemetry.db")
            if not db_path.exists():
                db_path = Path.home() / ".mimic_data" / "iss_telemetry.db"
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

    def calculate_orbital_parameters(self, pos_vec: list, vel_vec: list) -> dict:
        """Calculate accurate orbital parameters from state vectors."""
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
            
            # Calculate altitude (distance from Earth's surface)
            altitude_km = pos_mag - 6371.0  # Earth radius in km
            
            # Calculate specific angular momentum vector
            h_vec = cross(pos_vec, vel_vec)
            h_mag = math.sqrt(dot(h_vec, h_vec))
            
            # Calculate inclination (angle between h and z-axis)
            inc_rad = math.acos(safe_divide(h_vec[2], h_mag))
            inc_deg = math.degrees(inc_rad)
            
            # Calculate eccentricity vector
            v_radial = safe_divide(dot(vel_vec, pos_vec), pos_mag)
            
            # e = (v² - μ/r)r - (r·v)v / μ
            e_term1 = [x * (vel_mag**2 - mu/pos_mag) for x in pos_vec]
            e_term2 = [x * (pos_mag * v_radial) for x in vel_vec]
            e_vec = [(e_term1[i] - e_term2[i]) / mu for i in range(3)]
            e_mag = math.sqrt(dot(e_vec, e_vec))
            
            # Calculate orbital period
            # T = 2π * sqrt(a³/μ) where a is semi-major axis
            # a = h² / (μ(1-e²))
            if e_mag < 1:  # Valid orbit
                a = (h_mag**2) / (mu * (1 - e_mag**2))
                period_minutes = (2 * math.pi * math.sqrt(a**3 / mu)) / 60
            else:
                period_minutes = 0
            
            return {
                'altitude_km': altitude_km,
                'inc_deg': inc_deg,
                'period_minutes': period_minutes,
                'e_mag': e_mag
            }
            
        except Exception as exc:
            log_error(f"Calculate orbital parameters failed: {exc}")
            return {
                'altitude_km': 0,
                'inc_deg': 0,
                'period_minutes': 0,
                'beta_deg': 0,
                'e_mag': 0
            }

    def calculate_zoe_region(self) -> list:
        """Calculate the ZOE region - now returns static boundary."""
        try:
            return self.get_static_zoe_boundary()
        except Exception as exc:
            log_error(f"Calculate ZOE region failed: {exc}")
            return []

    def _clear_zoe_cache(self) -> None:
        """Clear the ZOE boundary cache to force recalculation."""
        self._zoe_boundary_cache = None
        self._zoe_cache_time = 0.0
        log_info("ZOE boundary cache cleared")

    def get_static_zoe_boundary(self) -> list:
        """Get a static ZOE boundary as a simple ellipse centered at 0° lat, 70° lon."""
        # Create a simple elliptical boundary
        center_lat = 0.0
        center_lon = 70.0
        lat_radius = 25.0  # ±25° latitude
        lon_radius = 20.0  # ±20° longitude
        
        # Generate ellipse points
        points = []
        num_points = 32  # Number of points to create smooth ellipse
        
        for i in range(num_points):
            angle = 2 * math.pi * i / num_points
            lat = center_lat + lat_radius * math.sin(angle)
            lon = center_lon + lon_radius * math.cos(angle)
            points.append((lat, lon))
        
        # Close the ellipse
        points.append(points[0])
        
        return points

    def is_point_in_zoe(self, lat: float, lon: float, zoe_boundary_points: list) -> bool:
        """Check if a point is inside the ZOE ellipse using simple distance check."""
        try:
            # Simple distance check from center
            center_lat = 0.0
            center_lon = 70.0
            lat_radius = 25.0
            lon_radius = 20.0
            
            # Calculate normalized distance from center
            lat_dist = abs(lat - center_lat) / lat_radius
            lon_dist = abs(lon - center_lon) / lon_radius
            
            # Point is inside if normalized distance <= 1
            return (lat_dist**2 + lon_dist**2) <= 1.0
            
        except Exception as exc:
            log_error(f"Check point in ZOE failed: {exc}")
            return False

    def calculate_zoe_timing(self) -> tuple:
        """Calculate time until ZOE entry and exit using static ZOE boundary."""
        try:
            if not self.iss_tle:
                return None, None
            
            # Get static ZOE boundary
            zoe_boundary_points = self.get_static_zoe_boundary()
            
            # Get current ISS position
            self.iss_tle.compute(ephem.now())
            current_lat = math.degrees(self.iss_tle.sublat)
            current_lon = math.degrees(self.iss_tle.sublong)
            
            # Check if currently in ZOE
            in_zoe = self.is_point_in_zoe(current_lat, current_lon, zoe_boundary_points)
            
            # Calculate future positions to find entry/exit times
            entry_time = None
            exit_time = None
            
            # Look ahead in time to find ZOE crossings
            current_time = ephem.now()
            
            # Use larger steps initially for efficiency, then refine
            coarse_step_minutes = 5
            
            # First pass: coarse search
            for i in range(1, 288):  # Look ahead 24 hours in 5-minute steps
                future_time = current_time + (i * coarse_step_minutes * ephem.minute)
                self.iss_tle.compute(future_time)
                future_lat = math.degrees(self.iss_tle.sublat)
                future_lon = math.degrees(self.iss_tle.sublong)
                
                future_in_zoe = self.is_point_in_zoe(future_lat, future_lon, zoe_boundary_points)
                
                if not in_zoe and future_in_zoe and entry_time is None:
                    entry_time = future_time
                elif in_zoe and not future_in_zoe and exit_time is None:
                    exit_time = future_time
                
                # Stop if we found both times
                if entry_time is not None and exit_time is not None:
                    break
            
            # If we're currently in ZOE, we need to find the next exit
            if in_zoe and exit_time is None:
                for i in range(1, 288):
                    future_time = current_time + (i * coarse_step_minutes * ephem.minute)
                    self.iss_tle.compute(future_time)
                    future_lat = math.degrees(self.iss_tle.sublat)
                    future_lon = math.degrees(self.iss_tle.sublong)
                    
                    future_in_zoe = self.is_point_in_zoe(future_lat, future_lon, zoe_boundary_points)
                    
                    if not future_in_zoe:
                        exit_time = future_time
                        break
            
            # If we're not in ZOE, we need to find the next entry
            if not in_zoe and entry_time is None:
                for i in range(1, 288):
                    future_time = current_time + (i * coarse_step_minutes * ephem.minute)
                    self.iss_tle.compute(future_time)
                    future_lat = math.degrees(self.iss_tle.sublat)
                    future_lon = math.degrees(self.iss_tle.sublong)
                    
                    future_in_zoe = self.is_point_in_zoe(future_lat, future_lon, zoe_boundary_points)
                    
                    if future_in_zoe:
                        entry_time = future_time
                        break
            
            return entry_time, exit_time
            
        except Exception as exc:
            log_error(f"Calculate ZOE timing failed: {exc}")
            return None, None

    def update_zoe_region(self) -> None:
        """Update the ZOE region display using static boundary."""
        try:
            # Get static ZOE boundary
            zoe_boundary_points = self.get_static_zoe_boundary()
            
            # Update timing labels
            entry_time, exit_time = self.calculate_zoe_timing()
            
            if 'zoe_loss_timer' in self.ids and 'zoe_acquisition_timer' in self.ids:
                current_time_ephem = ephem.now()
                
                # zoe_loss_timer shows time until ISS enters ZOE (loses signal)
                if entry_time and entry_time > current_time_ephem:
                    time_to_entry = entry_time - current_time_ephem
                    total_minutes = int(time_to_entry * 24 * 60)
                    minutes = total_minutes % 60
                    seconds = int((time_to_entry * 24 * 60 - total_minutes) * 60)
                    self.ids.zoe_loss_timer.text = f"{minutes:02d}:{seconds:02d}"
                else:
                    self.ids.zoe_loss_timer.text = "--:--"
                
                # zoe_acquisition_timer shows time until ISS exits ZOE (regains signal)
                if exit_time and exit_time > current_time_ephem:
                    time_to_exit = exit_time - current_time_ephem
                    total_minutes = int(time_to_exit * 24 * 60)
                    minutes = total_minutes % 60
                    seconds = int((time_to_exit * 24 * 60 - total_minutes) * 60)
                    self.ids.zoe_acquisition_timer.text = f"{minutes:02d}:{seconds:02d}"
                else:
                    self.ids.zoe_acquisition_timer.text = "--:--"
            
            # Update ZOE boundary display
            if 'ZOE_boundary' in self.ids and zoe_boundary_points:
                # Convert lat/lon points to screen coordinates
                screen_points = []
                for lat, lon in zoe_boundary_points:
                    x, y = self.map_px(lat, lon)
                    screen_points.extend([x, y])
                
                # Update the ZOE boundary widget
                for instruction in self.ids.ZOE_boundary.canvas.children:
                    if hasattr(instruction, 'points'):
                        instruction.points = screen_points
                        break
            
            # Update ZOE label position
            if 'ZOElabel' in self.ids:
                # Center of ZOE region
                zoe_center_lat = 0  # Equator
                zoe_center_lon = 70  # Center of Indian Ocean region
                x, y = self.map_px(zoe_center_lat, zoe_center_lon)
                self.ids.ZOElabel.pos = (x - self.ids.ZOElabel.width/2, y - self.ids.ZOElabel.height/2)
            
            # Check if ISS is currently in the ZOE
            if self.iss_tle and 'ZOE_boundary' in self.ids:
                self.iss_tle.compute(ephem.now())
                iss_lat = math.degrees(self.iss_tle.sublat)
                iss_lon = math.degrees(self.iss_tle.sublong)
                
                # Check if ISS is in ZOE
                in_zoe = self.is_point_in_zoe(iss_lat, iss_lon, zoe_boundary_points)
                
                if in_zoe:
                    # ISS is in ZOE - make it more visible
                    self.ids.ZOE_boundary.col = (1, 0, 0, 0.8)  # Red, more opaque
                else:
                    # ISS is not in ZOE - normal appearance
                    self.ids.ZOE_boundary.col = (1, 0, 1, 0.5)  # Magenta, semi-transparent
                        
        except Exception as exc:
            log_error(f"Update ZOE region failed: {exc}")

    def update_crew_sleep_timer(self) -> None:
        """Update the crew sleep timer based on standard sleep schedule (21:30-06:00 GMT)."""
        try:
            utc_now = datetime.utcnow()
            current_time = utc_now.time()
            
            # Define sleep schedule (21:30 to 06:00 GMT)
            sleep_start = datetime.strptime("21:30", "%H:%M").time()
            sleep_end = datetime.strptime("06:00", "%H:%M").time()
            
            # Check if currently in sleep period
            if sleep_start <= current_time or current_time < sleep_end:
                # During sleep period - show elapsed time
                if current_time < sleep_end:
                    # Sleep started yesterday at 21:30
                    sleep_start_dt = utc_now.replace(hour=21, minute=30, second=0, microsecond=0) - timedelta(days=1)
                else:
                    # Sleep started today at 21:30
                    sleep_start_dt = utc_now.replace(hour=21, minute=30, second=0, microsecond=0)
                
                elapsed = utc_now - sleep_start_dt
                hours = int(elapsed.total_seconds() // 3600)
                minutes = int((elapsed.total_seconds() % 3600) // 60)
                seconds = int(elapsed.total_seconds() % 60)
                
                self.ids.crew_sleep_timer.text = f"+{hours:02d}:{minutes:02d}:{seconds:02d}"
                self.ids.crew_sleep_timer.color = (0.5, 0, 0.5, 1)  # Magenta during sleep
            else:
                # Before sleep period - show countdown
                if current_time < sleep_start:
                    # Sleep starts today
                    sleep_start_dt = utc_now.replace(hour=21, minute=30, second=0, microsecond=0)
                else:
                    # Sleep starts tomorrow
                    sleep_start_dt = utc_now.replace(hour=21, minute=30, second=0, microsecond=0) + timedelta(days=1)
                
                countdown = sleep_start_dt - utc_now
                hours = int(countdown.total_seconds() // 3600)
                minutes = int((countdown.total_seconds() % 3600) // 60)
                seconds = int(countdown.total_seconds() % 60)
                
                self.ids.crew_sleep_timer.text = f"-{hours:02d}:{minutes:02d}:{seconds:02d}"
                self.ids.crew_sleep_timer.color = (1, 1, 1, 1)  # White countdown
                
        except Exception as exc:
            log_error(f"Update crew sleep timer failed: {exc}")
            self.ids.crew_sleep_timer.text = "Sleep: --:--"

    def update_telemetry_values(self) -> None:
        """Update all telemetry values using accurate state vectors."""
        try:
            # Get telemetry data from database
            values, timestamps = self.get_telemetry_data()

            if not values or len(values) < 61:
                log_error("Insufficient telemetry data")
                return
            
            # Extract ISS state vectors (indices 55-60 from GUI.py)
            position_x = float(values[55][0])  # km
            position_y = float(values[56][0])  # km
            position_z = float(values[57][0])  # km
            velocity_x = float(values[58][0]) / 1000.0  # convert to km/s
            velocity_y = float(values[59][0]) / 1000.0  # convert to km/s
            velocity_z = float(values[60][0]) / 1000.0  # convert to km/s
            
            # Get solar beta directly from telemetry (index 176 from GUI.py)
            solar_beta = float(values[176][0])  # degrees
            
            # Create position and velocity vectors
            pos_vec = [position_x, position_y, position_z]
            vel_vec = [velocity_x, velocity_y, velocity_z]
            
            # Calculate accurate orbital parameters
            orbital_params = self.calculate_orbital_parameters(pos_vec, vel_vec)
            
            # Calculate latitude and longitude from position vector
            # Convert Cartesian to spherical coordinates
            lat_rad = math.asin(position_z / math.sqrt(position_x**2 + position_y**2 + position_z**2))
            lon_rad = math.atan2(position_y, position_x)
            
            lat_deg = math.degrees(lat_rad)
            lon_deg = math.degrees(lon_rad)
            
            # Update UI elements with accurate values
            if 'latitude' in self.ids:
                self.ids.latitude.text = f"{lat_deg:.2f}°"
            if 'longitude' in self.ids:
                self.ids.longitude.text = f"{lon_deg:.2f}°"
            if 'altitude' in self.ids:
                self.ids.altitude.text = f"{orbital_params['altitude_km']:.1f} km"
            if 'inc' in self.ids:
                self.ids.inc.text = f"{orbital_params['inc_deg']:.2f}°"
            if 'period' in self.ids:
                self.ids.period.text = f"{orbital_params['period_minutes']:.1f}m"
            if 'solarbeta' in self.ids:
                self.ids.solarbeta.text = f"{solar_beta:.1f}°"
                
        except Exception as exc:
            log_error(f"Update telemetry values failed: {exc}")
            import traceback
            traceback.print_exc()

    def set_user_location(self, lat: float, lon: float) -> None:
        """Set the user location and update the display."""
        self.user_lat = lat
        self.user_lon = lon
        
        # Update the observer location for pass calculations
        self.location.lat = str(lat)
        self.location.lon = str(lon)
        
        # Update the display
        self.update_user_location()

    def on_size(self, *args):
        """Handle screen size changes for responsive design."""
        # Update user location when screen size changes
        Clock.schedule_once(self.update_user_location, 0.1)

    # ─────────────────────── map helper (root pixels) ──────────────────────────
    def map_px(self, lat: float, lon: float) -> tuple[float, float]:
        """
        lat/lon → root-pixel coordinates that you can assign to widget.pos.
        Works regardless of OrbitMap letter-boxing.
        """
        mp = self.ids.OrbitMap
        tw, th = mp.texture_size
        if tw == 0 or th == 0:
            return 0, 0                           # texture not loaded yet
    
        nw, nh = mp.norm_image_size
        pad_x  = (mp.width  - nw) / 2             # black bars left/right
        pad_y  = (mp.height - nh) / 2             # black bars top/bottom
    
        fx = (lon + 180.0) / 360.0                # west→east  0 … 1
        fy = (lat +  90.0) / 180.0                # north→south 0 … 1
    
        x = mp.x + pad_x + fx * nw
        y = mp.y + pad_y + fy * nh        # invert Y
        return x, y
    
    
    # ─────────────────────── Sun updater ───────────────────────────────────────
    def update_sun(self, _dt=0) -> None:
        if "sun_icon" not in self.ids:
            return                                # KV not built yet
    
        now = ephem.now()
        sun = ephem.Sun(now)
    
        # latitude = declination
        lat = degrees(sun.dec)
    
        # longitude: λ = RA − GST  (east-positive, wrap to −180…+180)
        g = ephem.Observer(); g.lon = '0'; g.lat = '0'; g.date = now
        lon = degrees(sun.ra - g.sidereal_time())
        lon = (lon + 180) % 360 - 180
    
        x, y = self.map_px(lat, lon)
        
        icon = self.ids.sun_icon
        icon.center = (x, y)
    
    # ---------------------------------------------------------------- files
    @property
    def map_jpg(self) -> Path:
        return Path.home() / ".mimic_data" / "map.jpg"

    @property
    def globe_png(self) -> Path:
        return Path.home() / ".mimic_data" / "globe.png"

    def update_orbit_map(self, _dt=0):
        self.ids.OrbitMap.source = str(self.map_jpg)
        self.ids.OrbitMap.reload()

    def update_globe_image(self, _dt=0):
        try:
            self.ids.orbit3d.source = str(self.globe_png)
            self.ids.orbit3d.reload()
        except Exception as exc:
            log_error(f"Globe image load error: {exc}")

    # ---------------------------------------------------------------- spawn helpers
    def update_globe(self, _dt=0):
        Popen(["python", f"{self.mimic_directory}/Mimic/Pi/orbitGlobe.py"])

    def update_nightshade(self, _dt=0):
        Popen(["python", f"{self.mimic_directory}/Mimic/Pi/NightShade.py"])

    def update_iss_tle(self, _dt=0):
        Popen(["python", f"{self.mimic_directory}/Mimic/Pi/getTLE_ISS.py"])

    def update_tdrs_tle(self, _dt=0):
        Popen(["python", f"{self.mimic_directory}/Mimic/Pi/getTLE_TDRS.py"])

    # ---------------------------------------------------------------- TDRS ground-track
    def update_tdrs(self, _dt=0):
        """Update TDRS positions and ground tracks."""
        try:
            log_info("Update TDRS")
            cfg = Path.home() / ".mimic_data" / "tdrs_tle_config.json"
            try:
                db = json.loads(cfg.read_text())
                # keep only the six satellites we actually display
                self.tdrs_tles = {
                    name: ephem.readtle(name, *lines)
                    for name, lines in db["TDRS_TLEs"].items()
                    if name in self._TDRS_IDS
                }
            except Exception as exc:
                log_error(f"TDRS TLE load failed: {exc}")
                return

            for name, sat in self.tdrs_tles.items():
                id_name = name.replace(" ", "")           # "TDRS 6" ? "TDRS6"
                if id_name not in self.ids:               # icon missing in KV ? skip
                    log_error(f"Missing KV id: {id_name}")
                    continue

                img = self.ids[id_name]                   # the small ellipse icon

                try:
                    sat.compute(datetime.utcnow())
                    lon = sat.sublong * 180 / math.pi      # ephem radians?deg
                    lat = sat.sublat  * 180 / math.pi
                except Exception as exc:
                    log_error(f"{name} compute failed: {exc}")
                    continue

                tex_w, tex_h  = self.ids.OrbitMap.texture_size
                norm_w, norm_h = self.ids.OrbitMap.norm_image_size
                nX = 1 if tex_w == 0 else norm_w / tex_w
                nY = 1 if tex_h == 0 else norm_h / tex_h

                x, y = self.map_px(lat, lon)        # root-pixel centre of the dot
                img.pos = (x - img.width  * nX / 2,
                           y - img.height * nY / 2)

                # Update ground track for this TDRS satellite
                track_id = f"{id_name}_track"
                if track_id in self.ids:
                    # Generate ground track points (simplified - one orbit ahead)
                    track_points = []
                    t = datetime.utcnow()
                    step = timedelta(minutes=1)
                    
                    for _ in range(1496):  # ~ one orbit ahead
                        try:
                            sat.compute(t)
                            track_lat = degrees(sat.sublat)
                            track_lon = degrees(sat.sublong)
                            track_x, track_y = self.map_px(track_lat, track_lon)
                            track_points.extend([track_x, track_y])
                            t += step
                        except Exception as exc:
                            log_error(f"{name} track compute failed: {exc}")
                            break
                    
                    # Update the track line
                    for instruction in self.ids[track_id].canvas.children:
                        if hasattr(instruction, 'points'):
                            instruction.points = track_points
                            break
                
                # Update active circle position if this TDRS is active
                circle_id = f"{id_name}_active_circle"
                if circle_id in self.ids:
                    circle_widget = self.ids[circle_id]
                    tdrs_id = int(name.split()[1])  # Extract TDRS number
                    if tdrs_id in self.active_tdrs:
                        circle_widget.center = img.center

            # Position TDRS labels dynamically based on satellite positions
            self._update_tdrs_labels()
        
            log_info("Update TDRS done")
            
        except Exception as exc:
            log_error(f"Update TDRS failed: {exc}")
            import traceback
            traceback.print_exc()

    # ---------------------------------------------------------------- ISS + next-pass
    def update_orbit(self, _dt=0):
        #log_info("Update Orbit")
        cfg = Path.home() / ".mimic_data" / "iss_tle_config.json"
        try:
            lines   = json.loads(cfg.read_text())
            self.iss_tle = ephem.readtle(
                "ISS (ZARYA)", lines["ISS_TLE_Line1"], lines["ISS_TLE_Line2"]
            )
        except Exception as exc:
            log_error(f"ISS TLE load failed: {exc}")
            return
    
        # --- observer (user location) ---------------------------------------
        loc             = self.location
        loc.lat, loc.lon = str(self.user_lat), str(self.user_lon)
        loc.elevation    = 10
        loc.date         = ephem.now()          # ← **reset each tick**
    
        # ----------------------------------------------------------------------
        try:
            next_pass = loc.next_pass(self.iss_tle)   # (AOS, …, max-el)
        except Exception as exc:
            log_error(f"next_pass failed: {exc}")
            return
        if next_pass[0] is None:      # never rises
            self.ids.iss_next_pass1.text = "n/a"
            self.ids.iss_next_pass2.text = "n/a"
            self.ids.countdown.text      = "n/a"
            return
    
        # — localise AOS time for display --------------------------------------
        utc_dt = datetime.strptime(str(next_pass[0]), "%Y/%m/%d %H:%M:%S")
        # For now, use Houston timezone. In the future, this could be configurable
        local  = utc_dt.replace(tzinfo=pytz.utc)\
                       .astimezone(pytz.timezone("America/Chicago"))
    
        self.ids.iss_next_pass1.text = local.strftime("%Y-%m-%d")
        self.ids.iss_next_pass2.text = local.strftime("%H:%M:%S")
    
        # — countdown ----------------------------------------------------------
        delta  = next_pass[0] - loc.date            # loc.date is *now*
        hrs    = delta * 24.0
        mins   = (hrs  - math.floor(hrs)) * 60
        secs   = (mins - math.floor(mins)) * 60
        self.ids.countdown.text = f"{int(hrs):02d}:{int(mins):02d}:{int(secs):02d}"
    
        # — visible / not visible flag ----------------------------------------
        sun         = ephem.Sun()
        loc.date    = next_pass[2]                  # max-elevation time
        sun.compute(loc)
        self.iss_tle.compute(loc)
        sun_alt = float(str(sun.alt).split(":")[0])
        self.ids.ISSvisible.text = (
            "Visible Pass!" if (not self.iss_tle.eclipsed and -18 < sun_alt < -6)
            else "Not Visible"
        )
        
        # — update orbit counters --------------------------------------------
        if 'dailyorbit' in self.ids and 'totalorbits' in self.ids:
            total_orbits = self.calculate_total_orbits()
            daily_orbits = self.calculate_daily_orbits()
            
            self.ids.totalorbits.text = str(total_orbits)
            self.ids.dailyorbit.text = str(daily_orbits)
        
        # — update telemetry values ------------------------------------------
        self.update_telemetry_values()
        
        # — update UTC time ------------------------------------------------
        if 'gmtime' in self.ids:
            utc_now = datetime.utcnow()
            self.ids.gmtime.text = utc_now.strftime("%H:%M:%S UTC")
        
        # — update crew sleep timer -----------------------------------------
        if 'crew_sleep_timer' in self.ids:
            self.update_crew_sleep_timer()
        
        # — update ZOE region ----------------------------------------------
        self.update_zoe_region()
        
    # ----------------------------------------------------------------- ISS icon + track
    def update_iss(self, _dt=0):
        """
        Update icon centre + rolling ground-track.
        """
        if "iss_icon" not in self.ids or self.iss_tle is None:
            return            # not ready yet

        # -- current sub-lat / sub-lon ---------------------------------------
        try:
            self.iss_tle.compute(datetime.utcnow())
            lat = degrees(self.iss_tle.sublat)
            lon = degrees(self.iss_tle.sublong)
        except Exception as exc:
            log_error(f"ISS compute failed: {exc}")
            return

        # -- icon position ---------------------------------------------------
        x, y = self.map_px(lat, lon)
        self.ids.iss_icon.center = (x, y)

    def update_groundtrack(self, _dt=0) -> None:
        """
        Draw one full upcoming orbit (~96 min) as two Line objects so the
        path wraps cleanly at +-180 degrees 
        """
        try:
            if self.iss_tle is None or "OrbitMap" not in self.ids:
                log_error("ISS TLE or OrbitMap not available")
                return

            # Check if track line widgets exist
            if "iss_track_line_a" not in self.ids or "iss_track_line_b" not in self.ids:
                log_error("Track line widgets not found in KV file")
                return

            #---------- propagate ISS one orbit ahead -----------------------------
            
            future_pts: list[tuple[float, float]] = []

            t = datetime.utcnow()                 # start time as real datetime
            step = timedelta(minutes=1)           # 60-s increments

            for _ in range(96):                   # ~ one orbit ahead
                self.iss_tle.compute(t)
                lat = degrees(self.iss_tle.sublat)
                lon = degrees(self.iss_tle.sublong)
                future_pts.append((lat, lon))
                t += step                         # advance to next minute

        

            # ---------- split where path crosses dateline ------------------------
            seg_a: list[float] = []
            seg_b: list[float] = []
            current = seg_a

            last_lon = future_pts[0][1]
            for lat, lon in future_pts:
                #if jump > 180, switch segments
                if abs(lon - last_lon) > 180:
                    current = seg_b if current is seg_a else seg_a
                x, y = self.map_px(lat, lon)
                current.extend([x, y])
                last_lon = lon

            # ---------- push to the Line widgets ---------------------------------
            # Access the line instructions directly from canvas
            for instruction in self.ids.iss_track_line_a.canvas.children:
                if hasattr(instruction, 'points'):
                    instruction.points = seg_a
                    break
            for instruction in self.ids.iss_track_line_b.canvas.children:
                if hasattr(instruction, 'points'):
                    instruction.points = seg_b
                    break
            
        except Exception as exc:
            log_error(f"Update ground track failed: {exc}")
            import traceback
            traceback.print_exc()

    def get_zoe_debug_info(self) -> dict:
        """Get debugging information about the current ZOE calculation."""
        try:
            info = {
                'cache_valid': False,
                'cache_age_seconds': 0,
                'boundary_points_count': 0,
                'iss_in_zoe': False,
                'tdrs_positions_count': 0,
                'tdrs_coverage_satellites': 'East (6,12) and West (10,11) only',
                'z_belt_excluded': 'TDRS 7,8 excluded (creates ZOE)',
                'iss_tle_available': self.iss_tle is not None,
                'iss_inclination': None,
            }
            
            # Check cache status
            current_time = time.time()
            if self._zoe_boundary_cache is not None:
                info['cache_valid'] = current_time - self._zoe_cache_time < self._zoe_cache_duration
                info['cache_age_seconds'] = current_time - self._zoe_cache_time
                info['boundary_points_count'] = len(self._zoe_boundary_cache)
            
            # Check TDRS positions
            tdrs_positions = self.get_tdrs_positions()
            info['tdrs_positions_count'] = len(tdrs_positions)
            
            # Check ISS position and ZOE status
            if self.iss_tle:
                self.iss_tle.compute(ephem.now())
                info['iss_inclination'] = math.degrees(self.iss_tle._inc)
                
                current_lat = math.degrees(self.iss_tle.sublat)
                current_lon = math.degrees(self.iss_tle.sublong)
                
                # Get current ZOE boundary
                zoe_boundary = self.get_static_zoe_boundary()
                if zoe_boundary:
                    info['iss_in_zoe'] = self.is_point_in_zoe(current_lat, current_lon, zoe_boundary)
            
            return info
            
        except Exception as exc:
            log_error(f"Get ZOE debug info failed: {exc}")
            return {'error': str(exc)}
