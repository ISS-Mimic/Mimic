from __future__ import annotations
from kivy.uix.screenmanager import Screen
import pathlib
from kivy.lang import Builder
from kivy.clock import Clock
import sqlite3
from pathlib import Path
from utils.logger import log_info, log_error
from ._base import MimicBase

kv_path = pathlib.Path(__file__).with_name("VV_Screen.kv")
Builder.load_file(str(kv_path))

class VV_Screen(MimicBase):
    """Visiting Vehicles overview screen."""

    _update_event = None

    def on_enter(self):
        try:
            self.update_vv_values(0)
            # Align with previous cadence
            self._update_event = Clock.schedule_interval(self.update_vv_values, 40)
            log_info("VV_Screen: started periodic VV updates (40s)")
        except Exception as exc:
            log_error(f"VV_Screen on_enter failed: {exc}")

    def on_leave(self):
        try:
            if self._update_event is not None:
                Clock.unschedule(self._update_event)
                self._update_event = None
                log_info("VV_Screen: stopped periodic VV updates")
        except Exception as exc:
            log_error(f"VV_Screen on_leave failed: {exc}")

    def _get_db_path(self) -> Path:
        shm = Path('/dev/shm/vv.db')
        if shm.exists():
            return shm
        fallback = Path.home() / '.mimic_data' / 'vv.db'
        return fallback

    def update_vv_values(self, _dt):
        """Query VV database and update VV screen widgets only."""
        try:
            db_path = self._get_db_path()
            if not db_path.exists():
                log_error(f"VV DB not found at {db_path}")
                self._clear_all()
                return

            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            # Verify table exists
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vehicles'")
            if cur.fetchone() is None:
                conn.close()
                log_error("Table 'vehicles' does not exist in vv.db")
                self._clear_all()
                return

            # Fetch columns
            cur.execute('SELECT Mission FROM vehicles')
            mission = cur.fetchall()
            cur.execute('SELECT Type FROM vehicles')
            mission_type = cur.fetchall()
            cur.execute('SELECT Location FROM vehicles')
            location = cur.fetchall()
            cur.execute('SELECT Arrival FROM vehicles')
            arrival = cur.fetchall()
            cur.execute('SELECT Departure FROM vehicles')
            departure = cur.fetchall()
            cur.execute('SELECT Spacecraft FROM vehicles')
            spacecraft = cur.fetchall()
            conn.close()

            all_ports = {
                "Node 2 Forward",
                "Node 2 Zenith",
                "Node 2 Nadir",
                "Node 1 Nadir",
                "Service Module Aft",
                "MRM-2 Zenith",
                "MRM-1 Nadir",
                "RS Node Nadir",
            }

            occupied_ports = set()

            # Reset dynamic text each pass
            # (Images are toggled per-vehicle and cleared for unoccupied ports later)
            self.ids.n2f_label.text = ""
            self.ids.n2z_label.text = ""
            self.ids.n2n_label.text = ""
            self.ids.n1n_label.text = ""
            self.ids.sma_label.text = ""
            self.ids.mrm2_label.text = ""
            self.ids.mrm1_label.text = ""
            self.ids.rsn_label.text = ""

            # Default off for all icons each pass
            for icon_id in (
                'n2f_dragon','n2f_starliner','n2z_dragon','n2z_starliner',
                'n1n_cygnus','n2n_htv_x','sma_soyuz','sma_progress',
                'mrm2_soyuz','mrm2_progress','mrm1_soyuz','mrm1_progress',
                'rsn_soyuz','rsn_progress',
            ):
                if icon_id in self.ids:
                    self.ids[icon_id].opacity = 0.0

            for i, loc_entry in enumerate(location):
                port = str(loc_entry[0]) if loc_entry and loc_entry[0] is not None else ""
                if not port:
                    continue
                occupied_ports.add(port)

                sc_raw = spacecraft[i][0] if spacecraft[i][0] is not None else ""
                sc_text = sc_raw.replace('\xa0', ' ').strip()
                mis_text = str(mission[i][0]) if mission[i][0] is not None else ""
                type_text = " (Crewed)" if str(mission_type[i][0]) == "Crewed" else " (Cargo)"

                # Normalize spacecraft names
                if any(tok in sc_text for tok in ("SC", "Boeing", "CST")):
                    sc_name = "CST-100 Starliner"
                    sc_name2 = sc_text
                elif "Crew" in sc_text:
                    sc_name = "Crew Dragon"
                    sc_name2 = sc_text.replace(sc_name + " ", "").strip()
                elif "Cargo" in sc_text:
                    sc_name = "Cargo Dragon"
                    sc_name2 = sc_text.replace(sc_name + " ", "").strip()
                elif "Soyuz" in sc_text:
                    sc_name = "Soyuz MS"
                    sc_name2 = sc_text.replace(sc_name + " ", "").strip()
                elif "Progress" in sc_text:
                    sc_name = "Progress MS"
                    sc_name2 = sc_text.replace(sc_name + " ", "").strip()
                elif "NG" in mis_text:
                    sc_name = "Cygnus"
                    sc_name2 = sc_text
                elif "HTV" in mis_text:
                    sc_name = "HTV-X"
                    sc_name2 = sc_text
                else:
                    sc_name = "n/a"
                    sc_name2 = "n/a"

                label_text = f"{sc_name}\n{mis_text}"

                # Toggle per-port widgets (VV screen only)
                if port == "Node 2 Forward":
                    self.ids.n2f_label.text = label_text
                    if "Dragon" in sc_name:
                        self.ids.n2f_dragon.opacity = 1.0
                    elif sc_name == "CST-100 Starliner":
                        self.ids.n2f_starliner.opacity = 1.0
                elif port == "Node 2 Zenith":
                    self.ids.n2z_label.text = label_text
                    if "Dragon" in sc_name:
                        self.ids.n2z_dragon.opacity = 1.0
                    elif sc_name == "CST-100 Starliner":
                        self.ids.n2z_starliner.opacity = 1.0
                elif port == "Node 2 Nadir":
                    self.ids.n2n_label.text = label_text
                    if "HTV" in sc_name:
                        self.ids.n2n_htv_x.opacity = 1.0
                    # Future: dreamchaser/htvx icons here
                elif port == "Node 1 Nadir":
                    self.ids.n1n_label.text = label_text
                    if sc_name == "Cygnus":
                        self.ids.n1n_cygnus.opacity = 1.0
                elif port == "Service Module Aft":
                    self.ids.sma_label.text = label_text
                    if "Soyuz" in sc_name:
                        self.ids.sma_soyuz.opacity = 1.0
                    elif "Progress" in sc_name:
                        self.ids.sma_progress.opacity = 1.0
                elif port == "MRM-2 Zenith":
                    self.ids.mrm2_label.text = label_text
                    if "Soyuz" in sc_name:
                        self.ids.mrm2_soyuz.opacity = 1.0
                    elif "Progress" in sc_name:
                        self.ids.mrm2_progress.opacity = 1.0
                elif port == "MRM-1 Nadir":
                    self.ids.mrm1_label.text = label_text
                    if "Soyuz" in sc_name:
                        self.ids.mrm1_soyuz.opacity = 1.0
                    elif "Progress" in sc_name:
                        self.ids.mrm1_progress.opacity = 1.0
                elif port == "RS Node Nadir":
                    self.ids.rsn_label.text = label_text
                    if "Soyuz" in sc_name:
                        self.ids.rsn_soyuz.opacity = 1.0
                    elif "Progress" in sc_name:
                        self.ids.rsn_progress.opacity = 1.0

            # Clear any unoccupied areas on VV screen
            unoccupied = all_ports - occupied_ports
            for port in unoccupied:
                if port == "Node 2 Forward":
                    self.ids.n2f_label.text = ""
                    self.ids.n2f_dragon.opacity = 0.0
                    self.ids.n2f_starliner.opacity = 0.0
                elif port == "Node 2 Zenith":
                    self.ids.n2z_label.text = ""
                    self.ids.n2z_dragon.opacity = 0.0
                    self.ids.n2z_starliner.opacity = 0.0
                elif port == "Node 2 Nadir":
                    self.ids.n2n_label.text = ""
                elif port == "Node 1 Nadir":
                    self.ids.n1n_label.text = ""
                    self.ids.n1n_cygnus.opacity = 0.0
                elif port == "Service Module Aft":
                    self.ids.sma_label.text = ""
                    self.ids.sma_soyuz.opacity = 0.0
                    self.ids.sma_progress.opacity = 0.0
                elif port == "MRM-2 Zenith":
                    self.ids.mrm2_label.text = ""
                    self.ids.mrm2_soyuz.opacity = 0.0
                    self.ids.mrm2_progress.opacity = 0.0
                elif port == "MRM-1 Nadir":
                    self.ids.mrm1_label.text = ""
                    self.ids.mrm1_soyuz.opacity = 0.0
                    self.ids.mrm1_progress.opacity = 0.0
                elif port == "RS Node Nadir":
                    self.ids.rsn_label.text = ""
                    self.ids.rsn_soyuz.opacity = 0.0
                    self.ids.rsn_progress.opacity = 0.0

        except Exception as exc:
            log_error(f"VV_Screen update failed: {exc}")
            self._clear_all()

    def _clear_all(self):
        # Clear labels
        for lid in ('n2f_label','n2z_label','n2n_label','n1n_label','sma_label','mrm2_label','mrm1_label','rsn_label'):
            if lid in self.ids:
                self.ids[lid].text = ""
        # Hide all icons
        for icon_id in (
            'n2f_dragon','n2f_starliner','n2z_dragon','n2z_starliner',
            'n1n_cygnus','sma_soyuz','sma_progress',
            'mrm2_soyuz','mrm2_progress','mrm1_soyuz','mrm1_progress',
            'rsn_soyuz','rsn_progress',
        ):
            if icon_id in self.ids:
                self.ids[icon_id].opacity = 0.0
