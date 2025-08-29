from __future__ import annotations
from kivy.uix.screenmanager import Screen
import pathlib
from kivy.lang import Builder
from kivy.clock import Clock
import sqlite3
from pathlib import Path
from utils.logger import log_info, log_error
from ._base import MimicBase

kv_path = pathlib.Path(__file__).with_name("RS_Screen.kv")
Builder.load_file(str(kv_path))

class RS_Screen(MimicBase):
    """Russian Segment Visiting Vehicles status screen."""

    _update_event = None

    def on_enter(self):
        try:
            self.update_rs_values(0)
            self._update_event = Clock.schedule_interval(self.update_rs_values, 40)
            log_info("RS_Screen: started periodic VV updates (40s)")
        except Exception as exc:
            log_error(f"RS_Screen on_enter failed: {exc}")

    def on_leave(self):
        try:
            if self._update_event is not None:
                Clock.unschedule(self._update_event)
                self._update_event = None
                log_info("RS_Screen: stopped periodic VV updates")
        except Exception as exc:
            log_error(f"RS_Screen on_leave failed: {exc}")

    def _get_db_path(self) -> Path:
        shm = Path('/dev/shm/vv.db')
        if shm.exists():
            return shm
        return Path.home() / '.mimic_data' / 'vv.db'

    def update_rs_values(self, _dt):
        try:
            db_path = self._get_db_path()
            if not db_path.exists():
                log_error(f"RS vv.db not found at {db_path}")
                self._clear_rs()
                return

            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vehicles'")
            if cur.fetchone() is None:
                conn.close()
                log_error("RS: table 'vehicles' missing")
                self._clear_rs()
                return

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
                "Service Module Aft",
                "MRM-2 Zenith",
                "MRM-1 Nadir",
                "RS Node Nadir",
            }

            occupied = set()

            # Defaults
            for lab in (
                'sma_mission','sma_vehicle','sma_spacecraft','sma_arrival','sma_departure',
                'mrm2_mission','mrm2_vehicle','mrm2_spacecraft','mrm2_arrival','mrm2_departure',
                'mrm1_mission','mrm1_vehicle','mrm1_spacecraft','mrm1_arrival','mrm1_departure',
                'rsn_mission','rsn_vehicle','rsn_spacecraft','rsn_arrival','rsn_departure',
            ):
                if lab in self.ids:
                    self.ids[lab].text = '-'

            for icon in (
                'sma_soyuz','sma_progress',
                'mrm2_soyuz','mrm2_progress',
                'mrm1_soyuz','mrm1_progress',
                'rsn_soyuz','rsn_progress',
            ):
                if icon in self.ids:
                    self.ids[icon].opacity = 0.0

            # Update from DB
            for i, loc_entry in enumerate(location):
                port = str(loc_entry[0]) if loc_entry and loc_entry[0] is not None else ""
                if not port or port not in all_ports:
                    continue
                occupied.add(port)

                sc_raw = spacecraft[i][0] if spacecraft[i][0] is not None else ""
                sc_text = sc_raw.replace('\xa0', ' ').strip()
                mis_text = str(mission[i][0]) if mission[i][0] is not None else ""
                type_text = " (Crewed)" if str(mission_type[i][0]) == "Crewed" else " (Cargo)"

                if "Soyuz" in sc_text:
                    sc_name = "Soyuz MS"
                    sc_name2 = sc_text.replace(sc_name + " ", "").strip()
                elif "Progress" in sc_text:
                    sc_name = "Progress MS"
                    sc_name2 = sc_text.replace(sc_name + " ", "").strip()
                else:
                    # other types shouldn't appear on RS ports
                    sc_name = sc_text or "n/a"
                    sc_name2 = sc_text or "n/a"

                arr_text = "Arrival: " + (str(arrival[i][0])[:10] if arrival[i][0] is not None else "-")
                dep_text = "Departure: " + (str(departure[i][0])[:10] if departure[i][0] is not None else "-")

                label_text = f"{sc_name}\n{mis_text}"

                if port == "Service Module Aft":
                    self.ids.sma_mission.text = mis_text + type_text
                    self.ids.sma_vehicle.text = sc_name
                    self.ids.sma_spacecraft.text = sc_name2
                    self.ids.sma_arrival.text = arr_text
                    self.ids.sma_departure.text = dep_text
                    self.ids.sma_label.text = label_text
                    if "Soyuz" in sc_name:
                        self.ids.sma_soyuz.opacity = 1.0
                    elif "Progress" in sc_name:
                        self.ids.sma_progress.opacity = 1.0
                elif port == "MRM-2 Zenith":
                    self.ids.mrm2_mission.text = mis_text + type_text
                    self.ids.mrm2_vehicle.text = sc_name
                    self.ids.mrm2_spacecraft.text = sc_name2
                    self.ids.mrm2_arrival.text = arr_text
                    self.ids.mrm2_departure.text = dep_text
                    self.ids.mrm2_label.text = label_text
                    if "Soyuz" in sc_name:
                        self.ids.mrm2_soyuz.opacity = 1.0
                    elif "Progress" in sc_name:
                        self.ids.mrm2_progress.opacity = 1.0
                elif port == "MRM-1 Nadir":
                    self.ids.mrm1_mission.text = mis_text + type_text
                    self.ids.mrm1_vehicle.text = sc_name
                    self.ids.mrm1_spacecraft.text = sc_name2
                    self.ids.mrm1_arrival.text = arr_text
                    self.ids.mrm1_departure.text = dep_text
                    self.ids.mrm1_label.text = label_text
                    if "Soyuz" in sc_name:
                        self.ids.mrm1_soyuz.opacity = 1.0
                    elif "Progress" in sc_name:
                        self.ids.mrm1_progress.opacity = 1.0
                elif port == "RS Node Nadir":
                    self.ids.rsn_mission.text = mis_text + type_text
                    self.ids.rsn_vehicle.text = sc_name
                    self.ids.rsn_spacecraft.text = sc_name2
                    self.ids.rsn_arrival.text = arr_text
                    self.ids.rsn_departure.text = dep_text
                    self.ids.rsn_label.text = label_text
                    if "Soyuz" in sc_name:
                        self.ids.rsn_soyuz.opacity = 1.0
                    elif "Progress" in sc_name:
                        self.ids.rsn_progress.opacity = 1.0

            # Clear unoccupied
            for port in (all_ports - occupied):
                if port == "Service Module Aft":
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
            log_error(f"RS_Screen update failed: {exc}")
            self._clear_rs()

    def _clear_rs(self):
        for lab in ('sma_label','mrm2_label','mrm1_label','rsn_label'):
            if lab in self.ids:
                self.ids[lab].text = ''
        for lab in (
            'sma_mission','sma_vehicle','sma_spacecraft','sma_arrival','sma_departure',
            'mrm2_mission','mrm2_vehicle','mrm2_spacecraft','mrm2_arrival','mrm2_departure',
            'mrm1_mission','mrm1_vehicle','mrm1_spacecraft','mrm1_arrival','mrm1_departure',
            'rsn_mission','rsn_vehicle','rsn_spacecraft','rsn_arrival','rsn_departure',
        ):
            if lab in self.ids:
                self.ids[lab].text = '-'
        for icon in (
            'sma_soyuz','sma_progress','mrm2_soyuz','mrm2_progress','mrm1_soyuz','mrm1_progress','rsn_soyuz','rsn_progress'
        ):
            if icon in self.ids:
                self.ids[icon].opacity = 0.0
