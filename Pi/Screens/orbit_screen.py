# Pi/Screens/orbit_screen.py
from __future__ import annotations

import json, math, time, pytz
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
        Clock.schedule_once(self.update_iss_tle,          14)
        Clock.schedule_once(self.update_tdrs_tle,          7)
        Clock.schedule_once(self.update_tdrs,             30)
        Clock.schedule_once(self.update_nightshade,       20)
        Clock.schedule_once(self.update_sun,              11) 

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
                log_error("missing KV id")
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


        x, y = self.map_px(0, 77)
        self.ids.ZOE.pos = (x - self.ids.ZOE.width / 2,
                            y - self.ids.ZOE.height / 2)

        self.ids.ZOElabel.pos = (x, y + 40) 
        self.ids.ZOE.color = (1,0,1,0.5)
    
        
        log_info("Update TDRS done")

    # ---------------------------------------------------------------- ISS + next-pass
    def update_orbit(self, _dt=0):
        log_info("Update Orbit")
        cfg = Path.home() / ".mimic_data" / "iss_tle_config.json"
        try:
            lines   = json.loads(cfg.read_text())
            self.iss_tle = ephem.readtle(
                "ISS (ZARYA)", lines["ISS_TLE_Line1"], lines["ISS_TLE_Line2"]
            )
        except Exception as exc:
            log_error(f"ISS TLE load failed: {exc}")
            return
    
        # --- observer (Houston for now) ---------------------------------------
        loc             = self.location
        loc.lat, loc.lon = "29.585736", "-95.1327829"
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

        if self.iss_tle is None or "OrbitMap" not in self.ids:
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
        self.ids.iss_track_line_a.line.points = seg_a
        self.ids.iss_track_line_b.line.points = seg_b
