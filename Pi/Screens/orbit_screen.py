# Pi/Screens/orbit_screen.py
from __future__ import annotations

import json, math, pytz, sqlite3
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

    # ---------------------------------------------------------------- enter
    def on_enter(self):
        log_info("Orbit Screen Initialized")
        
        # Debug: Check what widgets are available
        log_info(f"Available widget IDs: {list(self.ids.keys())}")
        
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
            
            # TLE epoch revolutions (from TLE line 2)
            # n is revolutions per day, so we need to calculate total revolutions at epoch
            revolutions_per_day = self.iss_tle.n
            days_since_launch = (epoch_dt - datetime(1998, 11, 20)).days  # ISS launched Nov 20, 1998
            epoch_revolutions = int(revolutions_per_day * days_since_launch)
            
            # Total = epoch revolutions + 100,000 + orbits since epoch
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
            
            # Calculate time since midnight
            time_since_midnight = (now_utc - midnight_utc).total_seconds()
            
            # ISS orbital period is approximately 92.5 minutes
            orbital_period_seconds = 92.5 * 60
            daily_orbits = int(time_since_midnight / orbital_period_seconds)
            
            return daily_orbits
            
        except Exception as exc:
            log_error(f"Calculate daily orbits failed: {exc}")
            return 0

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

            # Check if ZOE widgets exist before accessing them
            if 'ZOE' in self.ids and 'ZOElabel' in self.ids:
                x, y = self.map_px(0, 77)
                self.ids.ZOE.pos = (x - self.ids.ZOE.width / 2,
                                    y - self.ids.ZOE.height / 2)

                self.ids.ZOElabel.pos = (x, y + 40) 
                # Fix: ZOE is a Widget, not a Label, so we need to update the canvas color
                self.ids.ZOE.col = (1, 0, 1, 0.5)
            else:
                log_error("ZOE widgets not found in KV file")
        
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
