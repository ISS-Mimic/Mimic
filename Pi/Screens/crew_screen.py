from __future__ import annotations

# ───────────────────────── Imports ─────────────────────────
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import ListProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

from ._base import MimicBase
from utils.logger import log_error, log_info

# ──────────────────────── KV loading ───────────────────────
KV_PATH = Path(__file__).with_name("Crew_Screen.kv")
Builder.load_file(str(KV_PATH))

# ───────────────────── Configuration ───────────────────────
POLL_INTERVAL_S = 2.0         # fast polling until DB shows data
UPDATE_INTERVAL_S = 300.0     # periodic DB refresh
EXPEDITION_TICK_S = 1.0

# ──────────────────────── Widgets ──────────────────────────
class CrewMemberWidget(BoxLayout):
    """Individual crew member widget with photo, info, and stats."""

    name = StringProperty("")
    country = StringProperty("")
    spacecraft = StringProperty("")
    expedition = StringProperty("")
    mission_days = StringProperty("0")
    total_days = StringProperty("0")
    role = StringProperty("FE")
    mimic_directory = StringProperty("")
    image_url = StringProperty("")

    def __init__(self, crew_data: Dict, mimic_dir: str = "", **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = dp(200)
        self.padding = dp(10)
        self.spacing = dp(5)

        self.mimic_directory = mimic_dir

        self.name = crew_data.get("name", "Unknown")
        self.country = crew_data.get("country", "Unknown")
        self.spacecraft = crew_data.get("spaceship", "Unknown")
        self.expedition = crew_data.get("expedition", "Unknown")
        self.role = self._determine_role(crew_data)

        # Use DB-provided fields when present
        self.mission_days = str(crew_data.get("current_mission_duration", 0))
        self.total_days = str(crew_data.get("total_time_in_space", 0))
        
        # Set image URL and log it
        image_url = crew_data.get("image_url", "") or ""
        self.image_url = image_url
        
        if self.image_url:
            log_info(f"Crew member {self.name} image URL: {self.image_url}")
            # Force a property update to trigger the KV binding
            self.property('image_url').dispatch(self)
        else:
            log_info(f"Crew member {self.name} has no image URL, using fallback")

    def _determine_role(self, crew_data: Dict) -> str:
        """Map DB 'position' text into a compact role label."""
        position = (crew_data.get("position") or "").strip()
        pos_upper = position.upper()

        # Common role heuristics
        if "CDR" in pos_upper or "COMMAND" in pos_upper:
            return "CMDR"
        if "ENGINEER" in pos_upper or "FE" in pos_upper:
            return "FE"
        if "SPECIALIST" in pos_upper or "MS" in pos_upper:
            return "MS"
        if position:
            return position[:3].upper()
        if "Commander" in (crew_data.get("expedition") or ""):
            return "CMDR"
        return "FE"

    def update_image(self, new_url: str):
        """Update the image URL and force refresh."""
        if new_url != self.image_url:
            self.image_url = new_url
            log_info(f"Updated {self.name} image to: {new_url}")
            # Force the AsyncImage to reload
            self.property('image_url').dispatch(self)


# ──────────────────────── Screen ───────────────────────────
class Crew_Screen(MimicBase):
    """Dynamic crew screen that automatically displays current ISS crew."""

    crew_data = ListProperty([])
    expedition_number = StringProperty("Expedition 70")
    expedition_duration = StringProperty("0 days")
    iss_crewed_years = StringProperty("24")
    iss_crewed_months = StringProperty("9")
    iss_crewed_days = StringProperty("10")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.crew_widgets: List[CrewMemberWidget] = []
        self.update_timer = None
        self.poll_timer = None
        self.expedition_timer = None
        self._last_checksum = None  # Track database changes

    # ─────────────── Lifecycle & scheduling ────────────────
    def on_pre_enter(self):
        super().on_pre_enter()
        self._cancel_timer("update_timer")
        self._cancel_timer("poll_timer")
        self._cancel_timer("expedition_timer")

        self.load_crew_data()
        self._update_iss_crewed_time()
        self._update_expedition_duration()

        if self.crew_data:
            self.update_timer = Clock.schedule_interval(self.update_crew_data, UPDATE_INTERVAL_S)
        else:
            self.poll_timer = Clock.schedule_interval(self._poll_for_crew, POLL_INTERVAL_S)

        self.expedition_timer = Clock.schedule_interval(self._update_expedition_duration, EXPEDITION_TICK_S)

    def on_pre_leave(self):
        self._cancel_timer("update_timer")
        self._cancel_timer("poll_timer")
        self._cancel_timer("expedition_timer")
        super().on_pre_leave()

    def _cancel_timer(self, attr: str) -> None:
        t = getattr(self, attr, None)
        if t:
            try:
                t.cancel()
            except Exception:
                pass
            setattr(self, attr, None)

    # ────────────────── DB path (central) ──────────────────
    def get_db_path(self) -> str:
        """Get the database path using the centralized function."""
        try:
            from GUI import get_db_path as central_get_db_path
            db_path = central_get_db_path("iss_crew.db")
            log_info(f"Using DB: {db_path}")
            return db_path
        except Exception as e:
            log_error(f"get_db_path failed: {e}")
            # Fallback to local folder
            fallback = str(Path.cwd() / "iss_crew.db")
            log_info(f"Falling back to {fallback}")
            return fallback

    # ─────────────────── Data loading ──────────────────────
    def load_crew_data(self) -> None:
        """Load current crew from SQLite into self.crew_data and refresh UI only if changed."""
        try:
            db_path = self.get_db_path()
            p = Path(db_path)
            if not p.exists():
                log_info(f"Database not ready yet: {db_path}")
                self.crew_data = []
                self.update_crew_display()
                return

            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                
                # First check if data has changed by comparing checksums
                cur.execute("SELECT checksum FROM snapshots ORDER BY id DESC LIMIT 1")
                checksum_row = cur.fetchone()
                current_checksum = checksum_row[0] if checksum_row else None
                
                # If checksum hasn't changed, skip the update
                if current_checksum == self._last_checksum and self.crew_data:
                    log_info("Crew data unchanged, skipping update")
                    return
                
                log_info(f"Database checksum changed from {self._last_checksum} to {current_checksum}")
                self._last_checksum = current_checksum
                
                # Load the actual crew data
                cur.execute(
                    """
                    SELECT
                        name, country, spaceship, expedition, position,
                        launch_date, launch_time, landing_spacecraft,
                        landing_date, landing_time, mission_duration, orbits,
                        status, image_url, total_time_in_space, current_mission_duration
                    FROM current_crew
                    ORDER BY name
                    """
                )
                rows = cur.fetchall()

            self.crew_data = [dict(r) for r in rows]

            # Update expedition label (prefer explicit 'Expedition ##' value)
            self.expedition_number = self._extract_expedition_number()

            self.update_crew_display()
            self.update_expedition_patch()
            self._update_expedition_duration()

        except Exception as e:
            log_error(f"Error loading crew data: {e}")
            self.crew_data = []
            self.update_crew_display()

    # ──────────────────── UI updates ───────────────────────
    def update_crew_display(self) -> None:
        """Create/update crew member widgets."""
        try:
            crew_container = getattr(self.ids, "crew_container", None)
            if not crew_container or not hasattr(crew_container, "clear_widgets"):
                return

            crew_container.clear_widgets()
            self.crew_widgets.clear()

            for cd in self.crew_data:
                w = CrewMemberWidget(cd, mimic_dir=self.mimic_directory)
                crew_container.add_widget(w)
                self.crew_widgets.append(w)

            log_info(f"Updated crew display with {len(self.crew_data)} members")
        except Exception as e:
            log_error(f"Error updating crew display: {e}")

    # ──────────────── Time/duration helpers ────────────────
    def _parse_date(self, s: Optional[str]) -> Optional[datetime]:
        if not s:
            return None
        for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                continue
        return None

    def _duration_parts(self, start: datetime, end: Optional[datetime] = None) -> tuple[int, int, int]:
        """Approximate years, months, days using 365/30 rules (fits UI)."""
        end = end or datetime.now()
        total_days = max(0, (end - start).days)
        years = total_days // 365
        rem = total_days % 365
        months = rem // 30
        days = rem % 30
        return years, months, days

    def _format_parts(self, y: int, m: int, d: int) -> str:
        parts = []
        if y:
            parts.append(f"{y} year{'s' if y != 1 else ''}")
        if m:
            parts.append(f"{m} month{'s' if m != 1 else ''}")
        if d or not parts:
            parts.append(f"{d} day{'s' if d != 1 else ''}")
        return ", ".join(parts)

    def _format_counter(self, start: datetime, end: Optional[datetime] = None) -> str:
        """Format duration as mm:dd:hh:ss counter."""
        end = end or datetime.now()
        delta = end - start
        total_seconds = int(delta.total_seconds())
        
        if total_seconds < 0:
            return "00:00:00:00"
        
        days = total_seconds // 86400
        remaining_seconds = total_seconds % 86400
        hours = remaining_seconds // 3600
        minutes = (remaining_seconds % 3600) // 60
        seconds = remaining_seconds % 60
        
        return f"{days:02d}:{hours:02d}:{minutes:02d}:{seconds:02d}"

    def _format_expedition_duration(self, start: datetime, end: Optional[datetime] = None) -> str:
        """Format expedition duration as months, days, hours, seconds."""
        end = end or datetime.now()
        delta = end - start
        
        if delta.total_seconds() < 0:
            return "0 months, 0 days, 0 hours, 0 seconds"
        
        total_seconds = int(delta.total_seconds())
        
        # Calculate months (approximate - using 30 days per month)
        months = total_seconds // (30 * 24 * 3600)
        remaining_seconds = total_seconds % (30 * 24 * 3600)
        
        # Calculate days
        days = remaining_seconds // (24 * 3600)
        remaining_seconds = remaining_seconds % (24 * 3600)
        
        # Calculate hours
        hours = remaining_seconds // 3600
        remaining_seconds = remaining_seconds % 3600
        
        # Remaining seconds
        seconds = remaining_seconds
        
        # Build the formatted string
        parts = []
        if months > 0:
            parts.append(f"{months} m{'s' if months != 1 else ''}")
        if days > 0:
            parts.append(f"{days} d{'s' if days != 1 else ''}")
        if hours > 0:
            parts.append(f"{hours} h{'s' if hours != 1 else ''}")
        if seconds > 0 or not parts:  # Always show at least seconds
            parts.append(f"{seconds} s{'s' if seconds != 1 else ''}")
        
        return ", ".join(parts)

    # Expedition duration (oldest launch to now) - formatted as months, days, hours, seconds
    def _update_expedition_duration(self, *_):
        try:
            oldest = None
            for c in self.crew_data:
                dt = self._parse_date(c.get("launch_date"))
                if dt and (oldest is None or dt < oldest):
                    oldest = dt

            if oldest:
                self.expedition_duration = self._format_expedition_duration(oldest)
            else:
                self.expedition_duration = "0 months, 0 days, 0 hours, 0 seconds"
        except Exception as e:
            log_error(f"Error updating expedition duration: {e}")
            self.expedition_duration = "0 months, 0 days, 0 hours, 0 seconds"

    # "ISS crewed time" (since first crew on Nov 2, 2000)
    def _update_iss_crewed_time(self):
        try:
            # First ISS crew arrived on November 2nd, 2000 at 09:23 UTC
            first_crew_date = datetime(2000, 11, 2, 9, 23, 0)
            now = datetime.utcnow()
            
            y, m, d = self._duration_parts(first_crew_date, now)
            self.iss_crewed_years, self.iss_crewed_months, self.iss_crewed_days = map(str, (y, m, d))
            log_info(f"ISS crewed time: {y}y {m}m {d}d")
        except Exception as e:
            log_error(f"Error updating ISS crewed time: {e}")
            self.iss_crewed_years = self.iss_crewed_months = self.iss_crewed_days = "0"

    # ───────────────── Periodic updates ────────────────────
    def update_crew_data(self, _dt):
        """Periodic update - only refresh if database has changed."""
        self.load_crew_data()  # This now checks checksum internally
        self._update_iss_crewed_time()
        self.update_crewed_vehicles_display()

    def refresh_crew_data(self):
        log_info("Manual crew refresh requested")
        self.load_crew_data()
        self._update_iss_crewed_time()
        self.update_crewed_vehicles_display()

    # ─────────────── Crewed vehicles (VV DB) ───────────────
    def update_crewed_vehicles_display(self):
        try:
            vehicles = self.get_crewed_vehicles_from_vv_db()
            total_crew = sum(v.get("crew_count", 0) for v in vehicles)

            total_lbl = getattr(self.ids, "total_crew_count", None)
            if total_lbl:
                total_lbl.text = str(total_crew)

            self.update_crewed_vehicles_list(vehicles)
            log_info(f"Crewed vehicles: {len(vehicles)}; total crew: {total_crew}")
        except Exception as e:
            log_error(f"Error updating crewed vehicles display: {e}")

    def get_crewed_vehicles_from_vv_db(self) -> List[Dict]:
        try:
            from GUI import get_db_path
            vv_db_path = get_db_path("vv.db")
        except Exception as e:
            log_error(f"Could not resolve VV DB path: {e}")
            return []

        p = Path(vv_db_path)
        if not p.exists():
            log_error(f"VV database not found at {vv_db_path}")
            return []

        try:
            with sqlite3.connect(vv_db_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()

                # Verify table
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vehicles'")
                if not cur.fetchone():
                    log_error("Vehicles table not found in VV database")
                    return []

                cur.execute(
                    """
                    SELECT Mission, Spacecraft, Arrival, Location
                    FROM vehicles
                    WHERE Type = 'Crewed'
                    ORDER BY Arrival DESC
                    """
                )
                rows = cur.fetchall()

            def estimate_crew(spacecraft: str) -> int:
                s = (spacecraft or "").upper()
                if "CREW-" in s or "CREW " in s or "DRAGON" in s:
                    return 4
                if "SOYUZ" in s:
                    return 3
                # Default conservative
                return 3

            vehicles = []
            for r in rows:
                miss = str(r["Mission"]) if r["Mission"] is not None else "Unknown"
                sc = str(r["Spacecraft"]) if r["Spacecraft"] is not None else "Unknown"
                arr = str(r["Arrival"]) if r["Arrival"] is not None else "Unknown"
                loc = str(r["Location"]) if r["Location"] is not None else "Unknown"
                vehicles.append(
                    {
                        "mission": miss,
                        "spacecraft": sc,
                        "arrival": arr,
                        "location": loc,
                        "crew_count": estimate_crew(sc),
                    }
                )
            return vehicles
        except Exception as e:
            log_error(f"Error reading VV DB: {e}")
            return []

    def update_crewed_vehicles_list(self, vehicles: List[Dict]):
        try:
            container = getattr(self.ids, "crewed_vehicles_container", None)
            if not container or not hasattr(container, "clear_widgets"):
                return

            container.clear_widgets()
            for v in vehicles:
                container.add_widget(self._make_vehicle_widget(v))
        except Exception as e:
            log_error(f"Error updating vehicles list: {e}")

    def _make_vehicle_widget(self, vehicle: Dict) -> BoxLayout:
        widget = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(60))
        mission_label = Label(
            text=vehicle.get("mission", "Unknown"),
            color=(1, 1, 1, 1),
            font_size=dp(12),
            bold=True,
            size_hint_y=0.5,
        )
        info_label = Label(
            text=f"{vehicle.get('spacecraft','Unknown')}\nArrived: {vehicle.get('arrival','Unknown')}",
            color=(0.8, 0.8, 0.8, 1),
            font_size=dp(10),
            size_hint_y=0.5,
        )
        widget.add_widget(mission_label)
        widget.add_widget(info_label)
        return widget

    # ─────────────── Expedition patch image ────────────────
    def update_expedition_patch(self):
        try:
            patch_img = getattr(self.ids, "expedition_patch", None)
            if not patch_img:
                return

            m = re.search(r"Expedition\s+(\d+)", self.expedition_number or "")
            if not m:
                log_info("No expedition number parsed; not updating patch")
                return

            num = m.group(1)
            url = self._fetch_expedition_patch_from_wikipedia(num)
            if url:
                patch_img.source = url
                log_info(f"Expedition {num} patch updated")
        except Exception as e:
            log_error(f"Error updating expedition patch: {e}")

    def _fetch_expedition_patch_from_wikipedia(self, expedition_num: str) -> str:
        """Fetch/caches patch PNG from Wikipedia. Returns local path or ''."""
        try:
            import requests
            from bs4 import BeautifulSoup

            cache_dir = Path.home() / ".mimic_data" / "patches"
            cache_dir.mkdir(parents=True, exist_ok=True)
            cached = cache_dir / f"expedition_{expedition_num}_patch.png"
            if cached.exists():
                return str(cached)

            headers = {"User-Agent": "ISS Mimic Bot (https://github.com/ISS-Mimic; iss.mimic@gmail.com)"}
            page_url = f"https://en.wikipedia.org/wiki/Expedition_{expedition_num}"
            r = requests.get(page_url, headers=headers, timeout=10)
            r.raise_for_status()

            soup = BeautifulSoup(r.content, "html.parser")

            # Try to find a patch-like image in infobox first
            img = None
            infobox = soup.select_one(".infobox")
            if infobox:
                # common file naming: ISS_Expedition_XX_patch.png (or similar)
                img = infobox.select_one('img[src*="patch"]') or infobox.select_one('img[src*="Expedition"]')

            # fallback: any image on page that includes "patch"
            if not img:
                img = soup.select_one('img[src*="patch"]')

            if not img:
                log_info(f"No patch image found for Expedition {expedition_num}")
                return ""

            src = img.get("src", "")
            if not src:
                return ""

            if src.startswith("//"):
                full = "https:" + src
            elif src.startswith("/"):
                full = "https://en.wikipedia.org" + src
            else:
                full = src

            img_resp = requests.get(full, headers=headers, timeout=15)
            img_resp.raise_for_status()
            cached.write_bytes(img_resp.content)
            return str(cached)
        except Exception as e:
            log_error(f"Patch fetch failed for Expedition {expedition_num}: {e}")
            return ""

    # ───────────────────── Utilities ────────────────────────
    def _extract_expedition_number(self) -> str:
        """Choose a sensible expedition label from data."""
        for c in self.crew_data:
            exp = (c.get("expedition") or "").strip()
            if "Expedition" in exp:
                return exp
        return "Expedition 70"

    def _poll_for_crew(self, _dt):
        """Poll frequently until first data appears, then switch cadence."""
        prev_checksum = self._last_checksum
        self.load_crew_data()  # This now checks checksum internally
        
        # Check if we got new data (checksum changed)
        if self._last_checksum != prev_checksum and self.crew_data:
            self._cancel_timer("poll_timer")
            if not self.update_timer:
                self.update_timer = Clock.schedule_interval(self.update_crew_data, UPDATE_INTERVAL_S)
            Clock.schedule_once(lambda _t: self.update_crewed_vehicles_display(), 1.0)
