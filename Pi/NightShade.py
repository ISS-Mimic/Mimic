import datetime as dt
import math
from pathlib import Path

import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from cartopy.feature.nightshade import Nightshade
from shapely.geometry import Polygon
from shapely.ops import unary_union

# ---------------- Config (tweak as you like) ----------------
R_EARTH_KM = 6378.137
GEO_ALT_KM = 35786.0
GEO_R_KM = R_EARTH_KM + GEO_ALT_KM

# TDRS subsatellite longitudes (deg East; negative = West)
TDRS_LONS = [-45.0, -151.0, -174.0, -40.0]

# Default sampling and masks
DEFAULT_LAT_MIN = -52
DEFAULT_LAT_MAX = 52
DEFAULT_DLAT = 1.0  # deg
DEFAULT_DLON = 1.0  # deg
DEFAULT_E_MIN = 0.0  # deg elevation mask
DEFAULT_ALT_KM = 420.0  # observer altitude (ISS-ish)

# Image output
HOME = Path.home()
OUT_DIR = HOME / ".mimic_data"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_NOZOE = OUT_DIR / "map_nozoe.jpg"
OUT_ZOE = OUT_DIR / "map_zoe.jpg"
DPI = 150


# ---------------- Geometry helpers ----------------
def wrap_lon_deg(lon: float) -> float:
    x = ((lon + 180.0) % 360.0 + 360.0) % 360.0 - 180.0
    return 180.0 if x == -180.0 else x


def ecef_from_spherical(lat_deg, lon_deg, radius_km):
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    cl = math.cos(lat)
    return (
        radius_km * cl * math.cos(lon),
        radius_km * cl * math.sin(lon),
        radius_km * math.sin(lat),
    )


def vsub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vdot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def vnorm(a):
    m = math.hypot(a[0], a[1]);
    m = math.hypot(m, a[2])
    return (a[0] / m, a[1] / m, a[2] / m)


def elevation_deg_at_alt(lat_deg, lon_deg, h_km, sat_lon_deg):
    o = ecef_from_spherical(lat_deg, lon_deg, R_EARTH_KM + h_km)
    s = ecef_from_spherical(0.0, sat_lon_deg, GEO_R_KM)
    u = vsub(s, o)
    n = vnorm(o)
    sin_el = vdot(u, n) / math.sqrt(vdot(u, u))
    sin_el = max(-1.0, min(1.0, sin_el))
    return math.degrees(math.asin(sin_el))


def visible_any_tdrs(lat, lon, obs_alt_km, e_min_deg):
    for slon in TDRS_LONS:
        if elevation_deg_at_alt(lat, lon, obs_alt_km, slon) >= e_min_deg:
            return True
    return False


# ---------------- ZOE computation ----------------
def compute_no_coverage_rows(
        lat_min=DEFAULT_LAT_MIN, lat_max=DEFAULT_LAT_MAX,
        dlat=DEFAULT_DLAT, dlon=DEFAULT_DLON,
        e_min_deg=DEFAULT_E_MIN, obs_alt_km=DEFAULT_ALT_KM
):
    """
    Returns list of dict rows:
        [{'lat': <deg>, 'intervals': [(lon_start, lon_end), ...]}, ...]
    Intervals are non-coverage segments (inclusive) in [-180, 180].
    """
    lat_min, lat_max = sorted((max(-90.0, lat_min), min(90.0, lat_max)))
    dlat = max(0.1, float(dlat))
    dlon = max(0.1, float(dlon))

    rows = []
    steps_lon = int(round(360.0 / dlon))
    lat = lat_min
    while lat <= lat_max + 1e-9:
        intervals = []
        in_gap = False
        start = None
        for i in range(steps_lon + 1):
            lon = -180.0 + i * dlon
            gap = not visible_any_tdrs(lat, lon, obs_alt_km, e_min_deg)
            if gap and not in_gap:
                in_gap = True;
                start = lon
            if (not gap and in_gap) or (i == steps_lon and in_gap):
                end = 180.0 if (i == steps_lon and in_gap) else lon
                intervals.append((start, end))
                in_gap = False;
                start = None
        if intervals:
            rows.append({'lat': round(lat, 6), 'intervals': intervals})
        lat += dlat
    return rows


def build_no_coverage_polygons(rows, dlat=DEFAULT_DLAT):
    """
    Build shapely polygons (rectangles per row interval), merged.
    Handles dateline wrap by splitting into two rectangles.
    """
    rects = []
    for i in range(len(rows) - 1):
        lat1 = rows[i]['lat']
        lat2 = min(rows[i]['lat'] + dlat, rows[i + 1]['lat'])
        for (a, b) in rows[i]['intervals']:
            a = wrap_lon_deg(a);
            b = wrap_lon_deg(b)
            if a <= b:
                rects.append(Polygon([(a, lat1), (b, lat1), (b, lat2), (a, lat2), (a, lat1)]))
            else:
                # Wrap across the dateline
                rects.append(Polygon([(-180, lat1), (b, lat1), (b, lat2), (-180, lat2), (-180, lat1)]))
                rects.append(Polygon([(a, lat1), (180, lat1), (180, lat2), (a, lat2), (a, lat1)]))
    if not rects:
        return None
    return unary_union(rects)


# ---------------- Rendering ----------------
def _new_ax():
    fig = plt.figure(figsize=(10, 5))
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
    ax.stock_img()
    return fig, ax


def _draw_night(ax, when_utc: dt.datetime, alpha=0.25, zorder=5):
    ax.add_feature(Nightshade(when_utc, alpha=alpha), zorder=zorder)


def _draw_zoe(ax, poly, facecolor=(0.70, 0.49, 1.0), alpha=0.25, edgecolor='none', zorder=6):
    if poly and not poly.is_empty:
        ax.add_geometries([poly], crs=ccrs.PlateCarree(),
                          facecolor=facecolor, edgecolor=edgecolor, alpha=alpha, zorder=zorder)


def render_maps(
        out_dir=OUT_DIR,
        when_utc: dt.datetime | None = None,
        lat_min=DEFAULT_LAT_MIN, lat_max=DEFAULT_LAT_MAX,
        dlat=DEFAULT_DLAT, dlon=DEFAULT_DLON,
        e_min_deg=DEFAULT_E_MIN, obs_alt_km=DEFAULT_ALT_KM,
        dpi=DPI
):
    """
    Renders two images:
      - map_nozoe.jpg  (nightshade only)
      - map_zoe.jpg    (nightshade + ZOE overlay if present)
    Returns dict with paths and a boolean 'zoe_exists'.
    """
    when_utc = when_utc or dt.datetime.utcnow()
    out_dir = Path(out_dir);
    out_dir.mkdir(parents=True, exist_ok=True)
    path_nozoe = out_dir / "map_nozoe.jpg"
    path_zoe = out_dir / "map_zoe.jpg"

    # Compute ZOE once
    rows = compute_no_coverage_rows(lat_min, lat_max, dlat, dlon, e_min_deg, obs_alt_km)
    poly = build_no_coverage_polygons(rows, dlat=dlat)
    zoe_exists = bool(poly and not poly.is_empty)

    # --- map_nozoe ---
    fig1, ax1 = _new_ax()
    _draw_night(ax1, when_utc)
    fig1.savefig(path_nozoe, bbox_inches="tight", pad_inches=0, dpi=dpi)
    plt.close(fig1)

    # --- map_zoe ---
    fig2, ax2 = _new_ax()
    _draw_night(ax2, when_utc)
    _draw_zoe(ax2, poly)
    fig2.savefig(path_zoe, bbox_inches="tight", pad_inches=0, dpi=dpi)
    plt.close(fig2)


render_maps()

