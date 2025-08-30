from __future__ import annotations

import io
import math
import pathlib
from dataclasses import dataclass
from typing import Dict, List, Tuple

from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Rectangle
from kivy.lang import Builder
from kivy.properties import DictProperty, NumericProperty, ObjectProperty, StringProperty
from kivy.uix.widget import Widget

# ---------------------------------------------------------------------
# Project-local imports (kept, but safely optional so this file still runs standalone)
try:
    from ._base import MimicBase  # gives mimic_directory + signalcolor (your project base)
except Exception:  # pragma: no cover
    from kivy.uix.screenmanager import Screen as MimicBase  # fallback for standalone runs

try:
    from utils.logger import log_info, log_error
except Exception:  # pragma: no cover
    def log_info(msg): print("INFO:", msg)
    def log_error(msg): print("ERROR:", msg)
# ---------------------------------------------------------------------


# ---------- Matplotlib safe loader -----------------------------------
_matplotlib_ready = None


def _safe_import_matplotlib() -> bool:
    """Load matplotlib once (Agg backend) and cache success."""
    global _matplotlib_ready
    if _matplotlib_ready is not None:
        return _matplotlib_ready
    try:
        import matplotlib  # noqa: F401
        import matplotlib.pyplot as plt  # noqa: F401
        from matplotlib.backends.backend_agg import FigureCanvasAgg  # noqa: F401
        matplotlib.use("Agg")
        _matplotlib_ready = True
    except Exception as e:  # pragma: no cover
        log_error(f"Matplotlib import failed: {e}")
        _matplotlib_ready = False
    return _matplotlib_ready


# ---------- Simple sky chart widget ----------------------------------
class SkyChartWidget(Widget):
    """
    Draw a simple polar sky chart of an ISS pass.

    Input via set_pass_data():
      pass_data = {
        'azimuths': [deg...],      # len N
        'elevations': [deg...],    # len N
        'start_label': '08:02',
        'end_label': '08:07',
        'max_elev_deg': 67.2
      }
      user_location = (lat_deg, lon_deg)
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pass_data: Dict | None = None
        self.user_location: Tuple[float, float] | None = None
        # coalesce layout jitter into a single draw
        self._redraw_trigger = Clock.create_trigger(self._draw_chart, 0.12)
        self.bind(size=self._on_geom_change, pos=self._on_geom_change)

    def _on_geom_change(self, *_):
        if self.pass_data:
            self._redraw_trigger()

    def set_pass_data(self, pass_data: Dict, user_location: Tuple[float, float]):
        self.pass_data = pass_data
        self.user_location = user_location
        self._redraw_trigger()

    def _draw_chart(self, *_):
        self.canvas.clear()

        if not self.pass_data or not self.user_location:
            # placeholder background
            with self.canvas:
                Color(0.2, 0.2, 0.2, 1)
                Rectangle(pos=self.pos, size=self.size)
            return

        if not _safe_import_matplotlib():
            with self.canvas:
                Color(0.2, 0.2, 0.2, 1)
                Rectangle(pos=self.pos, size=self.size)
            return

        import matplotlib
        matplotlib.use("Agg")  # ensure Agg
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_agg import FigureCanvasAgg

        # Figure sized roughly to widget pixels (crisper text, fewer redraws)
        w = max(400, int(self.width))
        h = max(400, int(self.height))
        dpi = 110
        fig = plt.figure(figsize=(w / dpi, h / dpi), dpi=dpi)
        ax = fig.add_subplot(111, projection="polar")
        fig.patch.set_facecolor("white")
        ax.set_facecolor("white")

        # Polar config: N at top, clockwise azimuth; r=0 zenith, r=90 horizon
        ax.set_theta_zero_location("N")
        ax.set_theta_direction(-1)
        ax.set_rlim(90, 0)
        ax.set_rticks([0, 30, 60, 90])
        ax.grid(True, linewidth=0.6)

        # Cardinal labels
        for deg, lab in [(0, "N"), (90, "E"), (180, "S"), (270, "W")]:
            ax.text(math.radians(deg), 92, lab, ha="center", va="center",
                    fontsize=12, weight="bold")

        az = self.pass_data.get("azimuths") or []
        el = self.pass_data.get("elevations") or []
        if not az or not el or len(az) != len(el):
            plt.close(fig)
            with self.canvas:
                Color(0.2, 0.2, 0.2, 1)
                Rectangle(pos=self.pos, size=self.size)
            return

        thetas = [math.radians(a) for a in az]
        radii = [90.0 - e for e in el]

        ax.plot(thetas, radii, linewidth=2.6, label="ISS Pass")

        # Markers: start, max elev, end
        ax.plot(thetas[0], radii[0], "o", markersize=5)
        ax.plot(thetas[-1], radii[-1], "o", markersize=5)
        try:
            import numpy as np
            k_max = int(np.argmax(el))
        except Exception:
            k_max = max(range(len(el)), key=lambda i: el[i])
        ax.plot(thetas[k_max], radii[k_max], "o", markersize=6)

        # Title
        ax.set_title("ISS Pass", pad=10, fontsize=14, weight="bold")

        # Render to PNG in memory and let Kivy decode it
        canvas = FigureCanvasAgg(fig)
        canvas.draw()
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=dpi, facecolor=fig.get_facecolor(),
                    bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)

        ci = CoreImage(buf, ext="png")
        tex = ci.texture

        with self.canvas:
            Color(1, 1, 1, 1)
            Rectangle(texture=tex, pos=self.pos, size=self.size)


# ---------- The Screen ------------------------------------------------
kv_path = pathlib.Path(__file__).with_name("Orbit_Pass.kv")
Builder.load_file(str(kv_path))


@dataclass
class Location:
    lat: float = 29.55   # Houston default; replace with your persisted values
    lon: float = -95.09
    alt_m: float = 20.0


class Orbit_Pass(MimicBase):
    """
    ISS Pass detail screen with a simplified polar sky chart.
    """
    ui_scale = NumericProperty(1.0)
    location = ObjectProperty(Location())
    next_pass_data: DictProperty = DictProperty({})
    status_text = StringProperty("Pass not calculated yet.")

    def on_kv_post(self, *_):
        # initial UI scale + first render
        self.on_size()
        Clock.schedule_once(lambda *_: self.refresh_pass_data(), 0)

    def on_size(self, *_):
        # Scales typography across devices; 1280px baseline
        try:
            self.ui_scale = max(0.8, min(2.0, self.width / 1280.0))
        except Exception:
            self.ui_scale = 1.0

    # ---------------- Actions ----------------
    def update_location(self):
        """
        Hook this up to your real location loader (GPS, config, etc.).
        For now, it's a placeholder that just logs and re-draws.
        """
        log_info(f"Using location: lat={self.location.lat}, lon={self.location.lon}, alt={self.location.alt_m} m")
        self.refresh_pass_data()

    def refresh_pass_data(self):
        """
        Calculate (or fetch) the next ISS pass for the current location.
        Replace the stub with your actual pass calculation.
        """
        try:
            self.next_pass_data = self._calculate_next_pass_stub(self.location)
            self.status_text = f"Pass calculated: {self.next_pass_data.get('start_label', '')} - {self.next_pass_data.get('end_label', '')}"
            self._update_right_panel()
            self._update_sky_chart()
        except Exception as e:
            log_error(f"refresh_pass_data failed: {e}")
            self.status_text = "Failed to calculate pass."

    def _update_sky_chart(self):
        container = self.ids.get("sky_chart_container")
        if not container:
            return
        container.clear_widgets()
        chart = SkyChartWidget()
        chart.set_pass_data(self.next_pass_data, (self.location.lat, self.location.lon))
        container.add_widget(chart)

    def _update_right_panel(self):
        ids = self.ids
        # Safely set text on right column labels
        ids.max_elev_value.text = f"{self.next_pass_data.get('max_elev_deg', 0):.1f}°"
        ids.start_dir_value.text = f"{self.next_pass_data.get('start_az_deg', 0):.1f}°"
        ids.end_dir_value.text = f"{self.next_pass_data.get('end_az_deg', 0):.1f}°"
        ids.mag_value.text = f"{self.next_pass_data.get('magnitude', -1.5):.1f}"
        ids.start_time_value.text = self.next_pass_data.get("start_label", "--:--")
        ids.end_time_value.text = self.next_pass_data.get("end_label", "--:--")
        ids.duration_value.text = self.next_pass_data.get("duration_label", "--m")

    # ----------------- STUB: replace with real pass calc -----------------
    def _calculate_next_pass_stub(self, loc: Location) -> Dict:
        """
        Generates a plausible-looking pass arc and summary so the screen works.
        Replace with your real pass finder (SGP4/pyephem/skyfield/etc.)
        """
        # Build a nice, medium-high pass from az 245° → 114°, peak 67°
        import numpy as np

        n = 120  # points across the pass
        t = np.linspace(0, 1, n)
        # azimuth sweep clockwise from SW (245°) to ESE (114°) crossing south
        start_az, end_az = 245.0, 114.0
        # unwrap through 360 to keep a smooth monotonic curve
        az_path = np.linspace(start_az, 474.0, n)  # 114 + 360 = 474
        # basic bell for elevation, peak ~67°
        max_elev = 67.2
        elev = max_elev * np.sin(np.pi * t)
        elev[elev < 0] = 0

        # Summary labels
        start_label = "08:02"
        end_label = "08:07"
        duration_min = 5
        duration_label = f"{duration_min}m"

        return {
            "azimuths": az_path.tolist(),
            "elevations": elev.tolist(),
            "start_label": start_label,
            "end_label": end_label,
            "duration_label": duration_label,
            "max_elev_deg": max_elev,
            "start_az_deg": start_az,
            "end_az_deg": end_az,
            "magnitude": -1.5,
        }
