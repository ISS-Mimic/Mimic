from __future__ import annotations

import json
import math
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Tuple, List

import ephem
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import ListProperty, StringProperty, NumericProperty
from kivy.uix.widget import Widget
from kivy.uix.screenmanager import Screen
from kivy.graphics import Color, Line, Ellipse

from ._base import MimicBase
from utils.logger import log_info, log_error

# Load KV file at module level
try:
    kv_path = Path(__file__).with_name("Orbit_Pass.kv")
    Builder.load_file(str(kv_path))
    print("Orbit Pass: KV file loaded successfully")
except Exception as e:
    print(f"Orbit Pass: Failed to load KV file: {e}")
    import traceback
    traceback.print_exc()


# ------------------------------ small helpers ------------------------------

def _deg_to_card(deg: float) -> str:
    """16-wind compass cardinals."""
    dirs = [
        "N", "NNE", "NE", "ENE",
        "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW",
        "W", "WNW", "NW", "NNW",
    ]
    idx = int((deg % 360) / 22.5 + 0.5) % 16
    return dirs[idx]


def _fmt_time_local(utc_dt: datetime) -> str:
    """
    Render a UTC datetime in the machine's local timezone, e.g. '18:42:10'.
    We avoid hardcoding a specific tz so the Pi's localtime rules apply.
    """
    return utc_dt.replace(tzinfo=timezone.utc).astimezone().strftime("%H:%M:%S")


def _fmt_date_local(utc_dt: datetime) -> str:
    return utc_dt.replace(tzinfo=timezone.utc).astimezone().strftime("%Y-%m-%d")


def _est_visual_mag(iss_alt_deg: float, iss_range_m: float, phase_angle_rad: float) -> float:
    """
    Crude ISS visual magnitude estimate using elevation proxy (for phase) and range.
    - Baseline: ISS can reach about -5.5 at ~500 km and small phase angle.
    - We use a Lambertian-ish term with phase_angle and inverse-square with range.
    """
    # Clamp and convert
    rng_km = max(300.0, iss_range_m / 1000.0)  # avoid blow-ups at very small values
    # Baseline magnitude at 500 km near full phase
    M0 = -5.2
    # Range term (inverse square -> +5 log10(r))
    m_range = 5.0 * math.log10(rng_km / 500.0)
    # Phase term: 0 (brightest) .. pi (faintest); scale ~ 1.5–2.5 mag across full range
    m_phase = 2.0 * (phase_angle_rad / math.pi)
    return M0 + m_range + m_phase


def _phase_angle_rad(observer: ephem.Observer, iss: ephem.EarthSatellite, sun: ephem.Sun) -> float:
    """
    Phase angle at the ISS between (to Sun) and (to observer).
    """
    # Vector directions from ISS to Sun and to Observer (approximate using topocentric RA/Dec)
    # In PyEphem, we can compute at the observer, then use angular separation on the sky
    # as a cheap proxy for phase angle (not exact but good enough here).
    # angle between Sun and Observer directions as seen from ISS ~ angle between Sun and ISS as seen from Observer
    return abs(float(ephem.separation((sun.a_ra, sun.a_dec), (iss.a_ra, iss.a_dec))))


def _check_pass_visibility(observer: ephem.Observer,
                           iss: ephem.EarthSatellite,
                           when_utc: datetime,
                           min_el_deg: float = 10.0,
                           darkness_thresh_deg: float = -4.0,
                           moon_bright_penalty: bool = True) -> tuple[bool, dict]:
    """
    Returns (visible?, details) where details has fields useful for UI.
    Conditions:
      - ISS above min elevation
      - ISS sunlit (not eclipsed)
      - Sun below darkness threshold (tighten threshold if Moon is bright & high)
    """
    # Set time
    observer.date = ephem.Date(when_utc)
    # Compute bodies
    sun = ephem.Sun(observer)
    moon = ephem.Moon(observer)
    iss.compute(observer)

    sun_alt_deg = math.degrees(float(sun.alt))
    iss_el_deg  = math.degrees(float(iss.alt))
    iss_range_m = float(iss.range) if hasattr(iss, "range") else float('inf')

    # Adaptive darkness threshold if Moon is bright & high
    moon_alt_deg = math.degrees(float(moon.alt))
    moon_phase_pct = float(moon.phase)  # 0=new, 100=full
    adaptive_dark_thresh = darkness_thresh_deg
    if moon_bright_penalty and moon_phase_pct > 85.0 and moon_alt_deg > 10.0:
        # Make it a bit darker to count as "visible"
        adaptive_dark_thresh = min(-6.0, darkness_thresh_deg)

    # Basic visibility gates
    above_horizon = iss_el_deg >= min_el_deg
    sky_dark_enough = sun_alt_deg <= adaptive_dark_thresh

    # Sunlit test (preferred)
    sunlit = not bool(getattr(iss, "eclipsed", False))

    visible = above_horizon and sky_dark_enough and sunlit

    # Optional magnitude estimate
    try:
        phase_rad = _phase_angle_rad(observer, iss, sun)
        est_mag = _est_visual_mag(iss_el_deg, iss_range_m, phase_rad)
    except Exception:
        est_mag = None

    details = {
        "sun_alt_deg": sun_alt_deg,
        "moon_alt_deg": moon_alt_deg,
        "moon_phase_pct": moon_phase_pct,
        "iss_el_deg": iss_el_deg,
        "iss_range_km": None if math.isinf(iss_range_m) else iss_range_m / 1000.0,
        "iss_sunlit": sunlit,
        "darkness_threshold_deg": adaptive_dark_thresh,
        "est_mag": est_mag,
    }
    return visible, details


# ------------------------------ Sky chart widget ------------------------------

class SkyChart(Widget):
    """
    Simple zenithal sky chart.
    - track_points: [x0, y0, x1, y1, ...] polyline of the pass arc
    - start_xy / max_xy / end_xy: [x, y] markers
    """
    track_points = ListProperty([])
    start_xy = ListProperty([0.0, 0.0])
    max_xy = ListProperty([0.0, 0.0])
    end_xy = ListProperty([0.0, 0.0])

    def polar_xy(self, az_deg: float, el_deg: float) -> Tuple[float, float]:
        """
        Convert az/el to screen XY:
        - Center = zenith
        - r = edge at 0°, center at 90° (linear)
        - 0° az = North (up), increases clockwise (E at right)
        """
        R = max(0.0, min(self.width, self.height)) * 0.5 - self.dp(8)
        r = R * (90.0 - max(0.0, min(90.0, el_deg))) / 90.0
        th = math.radians(az_deg)
        x = self.center_x + r * math.sin(th)
        y = self.center_y + r * math.cos(th)
        return x, y

    @staticmethod
    def dp(px: float) -> float:
        # local helper to avoid import in this module
        from kivy.metrics import dp
        return dp(px)


# ------------------------------ Screen ------------------------------

class Orbit_Pass(MimicBase):
    """
    Displays the next ISS pass over user's location with a zenith sky plot.
    Logging follows the same pattern as other orbit screens.
    """

    # UI scaling property for responsive design
    ui_scale = NumericProperty(1.0)

    # For a friendly header
    pass_date_local = StringProperty("--")

    # ephem observers / satellites
    _observer: Optional[ephem.Observer] = None
    _iss: Optional[ephem.EarthSatellite] = None

    # schedule handles
    _evt_nextpass = None

    # cached user location
    _user_lat: float = 29.7604  # default Houston; overwritten by settings
    _user_lon: float = -95.3698

    def on_enter(self):
        try:
            log_info("Orbit Pass: on_enter()")
            
            self._load_user_location()
            self._load_iss_tle()
            self._build_observer()
            
            # Wait a frame for the UI to be ready, then compute pass
            Clock.schedule_once(self._delayed_pass_computation, 0.1)
            
        except Exception as exc:
            log_error(f"Orbit Pass init failed: {exc}")

    def _delayed_pass_computation(self, dt):
        """Compute pass after UI is ready."""
        try:
            log_info("Orbit Pass: Starting delayed pass computation")
            # compute now, then keep fresh
            self._update_next_pass(0)
            self._evt_nextpass = Clock.schedule_interval(self._update_next_pass, 30)
        except Exception as exc:
            log_error(f"Orbit Pass: Delayed pass computation failed: {exc}")

    def on_leave(self):
        log_info("Orbit Pass: on_leave() – unschedule timers")
        try:
            if self._evt_nextpass:
                Clock.unschedule(self._evt_nextpass)
        except Exception as exc:
            log_error(f"Orbit Pass unschedule failed: {exc}")

    def on_size(self, *args):
        """Handle screen size changes for UI scaling."""
        try:
            # Scale typography across devices; 1280px baseline
            self.ui_scale = max(0.8, min(2.0, self.width / 1280.0))
        except Exception:
            self.ui_scale = 1.0

    # ------------------------------ loaders ------------------------------

    def _load_user_location(self):
        """
        Mirrors Orbit Screen's settings loader so we're consistent.
        """
        try:
            cfg = Path.home() / ".mimic_data" / "location_config.json"
            if cfg.exists():
                data = json.loads(cfg.read_text())
                self._user_lat = float(data["lat"])
                self._user_lon = float(data["lon"])
                log_info(f"Orbit Pass: loaded user location {self._user_lat}, {self._user_lon}")
            else:
                log_error("Orbit Pass: location_config.json not found; using defaults")
        except Exception as exc:
            log_error(f"Orbit Pass: failed to load user location: {exc}")

    def _load_iss_tle(self):
        """
        Load ISS TLE previously fetched by your updater.
        """
        try:
            cfg = Path.home() / ".mimic_data" / "iss_tle_config.json"
            data = json.loads(cfg.read_text())
            l1 = data["ISS_TLE_Line1"]
            l2 = data["ISS_TLE_Line2"]
            self._iss = ephem.readtle("ISS", l1, l2)
            log_info("Orbit Pass: ISS TLE loaded")
        except Exception as exc:
            self._iss = None
            log_error(f"Orbit Pass: failed to load ISS TLE: {exc}")

    def _build_observer(self):
        try:
            obs = ephem.Observer()
            obs.lat = str(self._user_lat)
            obs.lon = str(self._user_lon)
            obs.elevation = 0
            obs.pressure = 0  # good enough for a pass chart
            # Prefer “visible” passes: raise horizon a bit so junk grazers are skipped
            obs.horizon = "5"  # degrees
            self._observer = obs
            log_info("Orbit Pass: observer constructed")
        except Exception as exc:
            self._observer = None
            log_error(f"Orbit Pass: failed to build observer: {exc}")

    # ------------------------------ compute & draw ------------------------------

    def _update_next_pass(self, _dt):
        """
        Compute the next pass and update labels + sky chart.
        """
        if not self._iss or not self._observer:
            log_error("Orbit Pass: missing ISS TLE or observer; cannot compute pass")
            return

        try:
            obs = self._observer
            obs.date = ephem.now()
            
            log_info(f"Orbit Pass: Computing pass for observer at {obs.lat}, {obs.lon}")
            log_info(f"Orbit Pass: Current time (UTC): {obs.date}")

            # PyEphem next_pass: rise_time, rise_az, max_time, max_alt, set_time, set_az
            # The next_pass method is on the Observer, not the satellite
            r_time, r_az, m_time, m_alt, s_time, s_az = obs.next_pass(self._iss)
            
            log_info(f"Orbit Pass: Pass computed - Rise: {r_time}, Max: {m_time}, Set: {s_time}")
            
            # Convert ephem.Date to UTC datetime for display
            r_dt = r_time.datetime()
            m_dt = m_time.datetime()
            s_dt = s_time.datetime()

            # Human fields
            rise_az_deg = float(r_az) * 180.0 / math.pi
            set_az_deg = float(s_az) * 180.0 / math.pi
            max_el_deg = float(m_alt) * 180.0 / math.pi

            duration_s = max(0, int((s_dt - r_dt).total_seconds()))
            dur_min = duration_s // 60
            dur_sec = duration_s % 60

            # Check if pass will be visible with detailed analysis
            pass_visible, visibility_details = _check_pass_visibility(self._observer, self._iss, m_dt)
            
            # Get magnitude from visibility details
            est_mag = visibility_details.get('est_mag')

            # Update info labels
            self.pass_date_local = _fmt_date_local(r_dt)
            ids = self.ids
            log_info(f"Orbit Pass: Updating UI labels, ids available: {list(ids.keys()) if hasattr(ids, 'keys') else 'No keys'}")
            
            if hasattr(ids, 'start_time'):
                ids.start_time.text = _fmt_time_local(r_dt)
                log_info(f"Orbit Pass: Updated start_time to {_fmt_time_local(r_dt)}")
            if hasattr(ids, 'start_az'):
                ids.start_az.text = f"{rise_az_deg:0.0f}° ({_deg_to_card(rise_az_deg)})"
                log_info(f"Orbit Pass: Updated start_az to {rise_az_deg:0.0f}° ({_deg_to_card(rise_az_deg)})")

            if hasattr(ids, 'max_time'):
                ids.max_time.text = _fmt_time_local(m_dt)
            if hasattr(ids, 'max_el'):
                ids.max_el.text = f"{max_el_deg:0.0f}°"
            if hasattr(ids, 'max_az'):
                ids.max_az.text = ""  # optional: could show az at max if desired

            if hasattr(ids, 'end_time'):
                ids.end_time.text = _fmt_time_local(s_dt)
            if hasattr(ids, 'end_az'):
                ids.end_az.text = f"{set_az_deg:0.0f}° ({_deg_to_card(set_az_deg)})"

            if hasattr(ids, 'duration'):
                ids.duration.text = f"{dur_min}m {dur_sec:02d}s"
            if hasattr(ids, 'magnitude'):
                if not pass_visible:
                    # Use visibility details to determine why not visible
                    sun_alt = visibility_details.get('sun_alt_deg', 0)
                    iss_sunlit = visibility_details.get('iss_sunlit', True)
                    iss_el = visibility_details.get('iss_el_deg', 0)
                    
                    if not iss_sunlit:
                        ids.magnitude.text = "Not visible (eclipsed)"
                    elif iss_el < 10.0:
                        ids.magnitude.text = "Not visible (too low)"
                    elif sun_alt > visibility_details.get('darkness_threshold_deg', -4.0):
                        ids.magnitude.text = "Not visible (too bright)"
                    else:
                        ids.magnitude.text = "Not visible (conditions)"
                elif est_mag is not None:
                    ids.magnitude.text = f"~{est_mag:0.1f} (est.)"
                else:
                    ids.magnitude.text = "Magnitude unknown"

            # Build sky path points
            pts, s_xy, m_xy, e_xy = self._build_sky_path(r_dt, s_dt, m_dt)
            if hasattr(ids, 'skychart'):
                schart: SkyChart = ids.skychart
                schart.track_points = pts
                schart.start_xy = list(s_xy)
                schart.max_xy = list(m_xy)
                schart.end_xy = list(e_xy)

            log_info(
                f"Orbit Pass: next pass {ids.start_time.text}–{ids.end_time.text}, "
                f"max {ids.max_el.text}"
            )
        except Exception as exc:
            log_error(f"Orbit Pass: pass compute failed: {exc}")

    def _build_sky_path(
        self, start_dt: datetime, end_dt: datetime, max_dt: datetime
    ) -> Tuple[List[float], Tuple[float, float], Tuple[float, float], Tuple[float, float]]:
        """
        Sample az/el along the pass; convert to XY for the sky chart.
        """
        ids = self.ids
        if not hasattr(ids, 'skychart'):
            log_error("Orbit Pass: skychart widget not found")
            return [], (0, 0), (0, 0), (0, 0)
        schart: SkyChart = ids.skychart

        # sample every 5s, clamp to sensible maximum
        step = 5
        total = max(1, int((end_dt - start_dt).total_seconds()))
        n = max(2, min(180, total // step))  # cap resolution
        points: List[float] = []

        # Convert helper: ephem.Date expects UTC; build once observer clone
        obs = ephem.Observer()
        obs.lat = str(self._user_lat)
        obs.lon = str(self._user_lon)
        obs.elevation = 0
        obs.pressure = 0

        def azel_at(tdt: datetime) -> Tuple[float, float]:
            # Convert Python datetime to ephem.Date and compute topocentric at observer
            ephem_date = ephem.Date(tdt)
            obs.date = ephem_date
            self._iss.compute(obs)
            # az, alt in radians -> degrees
            return float(self._iss.az) * 180.0 / math.pi, float(self._iss.alt) * 180.0 / math.pi

        # start / max / end markers first
        s_az, s_el = azel_at(start_dt)
        m_az, m_el = azel_at(max_dt)
        e_az, e_el = azel_at(end_dt)

        s_xy = schart.polar_xy(s_az, s_el)
        m_xy = schart.polar_xy(m_az, m_el)
        e_xy = schart.polar_xy(e_az, e_el)

        # build track polyline
        t = start_dt
        delta = timedelta(seconds=step)
        for _ in range(n + 1):
            az, el = azel_at(t)
            # only draw portion above horizon (>= 0°)
            if el >= 0.0:
                x, y = schart.polar_xy(az, el)
                points.extend([x, y])
            t += delta

        # Ensure we at least have endpoints
        if not points:
            points.extend([*s_xy, *e_xy])

        log_info(f"Orbit Pass: sky path points={len(points)//2}, start={s_xy}, max={m_xy}, end={e_xy}")

        return points, s_xy, m_xy, e_xy
