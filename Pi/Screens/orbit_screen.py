# Pi/Screens/orbit_screen.py
from __future__ import annotations

import json, math, time, logging
from datetime import datetime, timedelta
from pathlib import Path
from subprocess import Popen
from typing import Optional

import ephem, pytz
from kivy.clock import Clock
from kivy.lang import Builder

from ._base import MimicBase

log_info  = logging.getLogger("MyLogger").info
log_error = logging.getLogger("MyLogger").error

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
        print("orbit screen on enter")
        # periodic updates
        Clock.schedule_interval(self.update_orbit,         1)
        Clock.schedule_interval(self.update_nightshade,  120)
        Clock.schedule_interval(self.update_orbit_map,    31)
        Clock.schedule_interval(self.update_globe_image,  55)
        Clock.schedule_interval(self.update_globe,        31)
        Clock.schedule_interval(self.update_tdrs,        607)

        # one-shots that existed in MainApp.build()
        Clock.schedule_once(self.update_iss_tle,         14)
        Clock.schedule_once(self.update_tdrs_tle,         7)
        Clock.schedule_interval(self.update_tdrs,        30)
        Clock.schedule_interval(self.update_nightshade,  20)

    # ─────────────── helpers used by many orbit functions ──────────────────
    @staticmethod
    def scale_latlon(lat: float, lon: float) -> dict[str, float]:
        print("scale latlon")
        """
        Convert (lat, lon) to Kivy pos_hint percentages.
        Returns keys **center_x / center_y** so callers can use it directly.
        """
        center_y = 0.265 + (lat + 90)  / 180.0 * 0.598
        center_x = 0.140 + (lon + 180) / 360.0 * 0.716
        return {"center_x": center_x, "center_y": center_y}

    # ---------------------------------------------------------------- files
    @property
    def map_jpg(self) -> Path:
        return Path.home() / ".mimic_data" / "map.jpg"

    @property
    def globe_png(self) -> Path:
        return Path.home() / ".mimic_data" / "globe.png"

    # ---------------------------------------------------------------- image reloads
    def update_orbit_map(self, _dt=0):
        print("update orbit map")
        self.ids.OrbitMap.source = str(self.map_jpg)
        self.ids.OrbitMap.reload()

    def update_globe_image(self, _dt=0):
        print("update globe image")
        try:
            self.ids.orbit3d.source = str(self.globe_png)
            self.ids.orbit3d.reload()
        except Exception as exc:
            log_error(f"Globe image load error: {exc}")

    # ---------------------------------------------------------------- spawn helpers
    def update_globe(self, _dt=0):
        print("update globe")
        Popen(["python", f"{self.mimic_directory}/Mimic/Pi/orbitGlobe.py"])

    def update_nightshade(self, _dt=0):
        print("update nightshade")
        Popen(["python", f"{self.mimic_directory}/Mimic/Pi/NightShade.py"])

    def update_iss_tle(self, _dt=0):
        print("update iss tle")
        Popen(["python", f"{self.mimic_directory}/Mimic/Pi/getTLE_ISS.py"])

    def update_tdrs_tle(self, _dt=0):
        print("update tdrs tle")
        Popen(["python", f"{self.mimic_directory}/Mimic/Pi/getTLE_TDRS.py"])

    # ---------------------------------------------------------------- TDRS ground-track
    def update_tdrs(self, _dt=0):
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
            print(f"TDRS TLE load failed: {exc}")
            log_error(f"TDRS TLE load failed: {exc}")
            return

        def safe_div(a, b): return 1 if b == 0 else a / b
        nX = safe_div(self.ids.OrbitMap.norm_image_size[0],
                      self.ids.OrbitMap.texture_size[0])
        nY = safe_div(self.ids.OrbitMap.norm_image_size[1],
                      self.ids.OrbitMap.texture_size[1])

        for name, sat in self.tdrs_tles.items():
            id_name = name.replace(" ", "")           # "TDRS 6" ? "TDRS6"
            if id_name not in self.ids:               # icon missing in KV ? skip
                print("missing KV id")
                continue

            img = self.ids[id_name]                   # the small ellipse icon

            try:
                sat.compute(datetime.utcnow())
                lon = sat.sublong * 180 / math.pi      # ephem radians?deg
                lat = sat.sublat  * 180 / math.pi
            except Exception as exc:
                log_error(f"{name} compute failed: {exc}")
                continue

            pos = self.scale_latlon(lat, lon)
            tex, norm = self.ids.OrbitMap.texture_size, self.ids.OrbitMap.norm_image_size
            nX = 1 if tex[0] == 0 else norm[0] / tex[0]
            nY = 1 if tex[1] == 0 else norm[1] / tex[1]

            img.pos = (
                (pos["center_x"] * tex[0]) - img.width  / 2 * nX,
                (pos["center_y"] * tex[1]) - img.height / 2 * nY,
            )

        pos = self.scale_latlon(0, 77)
        self.ids.ZOE.pos_hint       = pos
        self.ids.ZOElabel.pos_hint  = {"center_x": pos["center_x"],
                                       "center_y": pos["center_y"] + 0.1}
        #print(self.ids.ZOE.pos_hint)

    # ---------------------------------------------------------------- ISS + next-pass
    def update_orbit(self, _dt=0):
        #print("update orbit")
        cfg = Path.home() / ".mimic_data" / "iss_tle_config.json"
        try:
            lines = json.loads(cfg.read_text())
            #print("orbit iss json")
            self.iss_tle = ephem.readtle(
                "ISS (ZARYA)", lines["ISS_TLE_Line1"], lines["ISS_TLE_Line2"]
            )
            #print(self.iss_tle)
        except Exception as exc:
            log_error(f"ISS TLE load failed: {exc}")
            return

        # compute next pass for Houston - hard coded for now
        loc = self.location
        loc.lat, loc.lon = "29.585736", "-95.1327829"
        loc.elevation    = 10

        try:
            next_pass = loc.next_pass(self.iss_tle)
        except Exception as exc:
            log_error(f"next_pass failed: {exc}")
            return

        if next_pass[0] is None:
            self.ids.iss_next_pass1.text = "n/a"
            self.ids.iss_next_pass2.text = "n/a"
            self.ids.countdown.text      = "n/a"
            return

        # localise
        utc_dt  = datetime.strptime(str(next_pass[0]), "%Y/%m/%d %H:%M:%S")
        local   = utc_dt.replace(tzinfo=pytz.utc).astimezone(
                    pytz.timezone("America/Chicago"))

        self.ids.iss_next_pass1.text = str(local).split()[0]
        self.ids.iss_next_pass2.text = str(local).split()[1].split('-')[0]

        delta   = next_pass[0] - loc.date
        hrs     = delta * 24.0
        mins    = (hrs - math.floor(hrs)) * 60
        secs    = (mins - math.floor(mins)) * 60
        self.ids.countdown.text = f"{int(hrs):02d}:{int(mins):02d}:{int(secs):02d}"

        # simple visible / not-visible flag
        sun = ephem.Sun(); loc.date = next_pass[2]  # max elevation time
        sun.compute(loc); self.iss_tle.compute(loc)
        sun_alt = float(str(sun.alt).split(':')[0])
        self.ids.ISSvisible.text = (
            "Visible Pass!" if not self.iss_tle.eclipsed and -18 < sun_alt < -6
            else "Not Visible"
        )
