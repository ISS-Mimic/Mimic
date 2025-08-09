from __future__ import annotations
from kivy.uix.screenmanager import Screen
import pathlib
from kivy.lang import Builder
from kivy.clock import Clock
import sqlite3
from pathlib import Path
from utils.logger import log_info, log_error
from ._base import MimicBase

kv_path = pathlib.Path(__file__).with_name("USOS_Screen.kv")
Builder.load_file(str(kv_path))

class USOS_Screen(MimicBase):
    """USOS Visiting Vehicle dock status screen."""

    _update_event = None

    def on_enter(self):
        try:
            self.update_usos_values(0)
            self._update_event = Clock.schedule_interval(self.update_usos_values, 40)
            log_info("USOS_Screen: started periodic VV updates (40s)")
        except Exception as exc:
            log_error(f"USOS_Screen on_enter failed: {exc}")

    def on_leave(self):
        try:
            if self._update_event is not None:
                Clock.unschedule(self._update_event)
                self._update_event = None
                log_info("USOS_Screen: stopped periodic VV updates")
        except Exception as exc:
            log_error(f"USOS_Screen on_leave failed: {exc}")

    def _get_db_path(self) -> Path:
        shm = Path('/dev/shm/vv.db')
        if shm.exists():
            return shm
        return Path.home() / '.mimic_data' / 'vv.db'

    def update_usos_values(self, _dt):
        try:
            db_path = self._get_db_path()
            if not db_path.exists():
                log_error(f"USOS vv.db not found at {db_path}")
                self._clear_usos()
                return

            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vehicles'")
            if cur.fetchone() is None:
                conn.close()
                log_error("USOS: table 'vehicles' missing")
                self._clear_usos()
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
                "Node 2 Forward",
                "Node 2 Zenith",
                "Node 2 Nadir",
                "Node 1 Nadir",
            }

            occupied = set()

            # Defaults each pass
            for lab in (
                'n2f_mission','n2f_vehicle','n2f_spacecraft','n2f_arrival','n2f_departure',
                'n2z_mission','n2z_vehicle','n2z_spacecraft','n2z_arrival','n2z_departure',
                'n2n_mission','n2n_vehicle','n2n_spacecraft','n2n_arrival','n2n_departure',
                'n1n_mission','n1n_vehicle','n1n_spacecraft','n1n_arrival','n1n_departure',
            ):
                if lab in self.ids:
                    self.ids[lab].text = "-"

            for icon in ('n2f_dragon','n2f_starliner','n2z_dragon','n2z_starliner','n1n_cygnus','n2n_cygnus'):
                if icon in self.ids:
                    self.ids[icon].opacity = 0.0

            # Update from DB
            for i, loc_entry in enumerate(location):
                port = str(loc_entry[0]) if loc_entry and loc_entry[0] is not None else ""
                if not port:
                    continue
                if port not in all_ports:
                    continue
                occupied.add(port)

                sc_raw = spacecraft[i][0] if spacecraft[i][0] is not None else ""
                sc_text = sc_raw.replace('\xa0', ' ').strip()
                mis_text = str(mission[i][0]) if mission[i][0] is not None else ""
                type_text = " (Crewed)" if str(mission_type[i][0]) == "Crewed" else " (Cargo)"

                if any(tok in sc_text for tok in ("SC","Boeing","CST")):
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
                else:
                    sc_name = "n/a"
                    sc_name2 = "n/a"

                arr_text = "Arrival: " + (str(arrival[i][0])[:10] if arrival[i][0] is not None else "-")
                dep_text = "Departure: " + (str(departure[i][0])[:10] if departure[i][0] is not None else "-")

                if port == "Node 2 Forward":
                    self.ids.n2f_mission.text = mis_text + type_text
                    self.ids.n2f_vehicle.text = sc_name
                    self.ids.n2f_spacecraft.text = sc_name2
                    self.ids.n2f_arrival.text = arr_text
                    self.ids.n2f_departure.text = dep_text
                    self.ids.n2f_label.text = f"{sc_name}\n{mis_text}"
                    if "Dragon" in sc_name:
                        self.ids.n2f_dragon.opacity = 1.0
                    elif sc_name == "CST-100 Starliner":
                        self.ids.n2f_starliner.opacity = 1.0
                elif port == "Node 2 Zenith":
                    self.ids.n2z_mission.text = mis_text + type_text
                    self.ids.n2z_vehicle.text = sc_name
                    self.ids.n2z_spacecraft.text = sc_name2
                    self.ids.n2z_arrival.text = arr_text
                    self.ids.n2z_departure.text = dep_text
                    self.ids.n2z_label.text = f"{sc_name}\n{mis_text}"
                    if "Dragon" in sc_name:
                        self.ids.n2z_dragon.opacity = 1.0
                    elif sc_name == "CST-100 Starliner":
                        self.ids.n2z_starliner.opacity = 1.0
                elif port == "Node 2 Nadir":
                    self.ids.n2n_mission.text = mis_text + type_text
                    self.ids.n2n_vehicle.text = sc_name
                    self.ids.n2n_spacecraft.text = sc_name2
                    self.ids.n2n_arrival.text = arr_text
                    self.ids.n2n_departure.text = dep_text
                    self.ids.n2n_label.text = f"{sc_name}\n{mis_text}"
                    # Icons for n2n not currently defined
                elif port == "Node 1 Nadir":
                    self.ids.n1n_mission.text = mis_text + type_text
                    self.ids.n1n_vehicle.text = sc_name
                    self.ids.n1n_spacecraft.text = sc_name2
                    self.ids.n1n_arrival.text = arr_text
                    self.ids.n1n_departure.text = dep_text
                    self.ids.n1n_label.text = f"{sc_name}\n{mis_text}"
                    if sc_name == "Cygnus":
                        self.ids.n1n_cygnus.opacity = 1.0

            # Clear unoccupied
            for port in (all_ports - occupied):
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

        except Exception as exc:
            log_error(f"USOS_Screen update failed: {exc}")
            self._clear_usos()

    def _clear_usos(self):
        # reset labels
        for lab in ('n2f_label','n2z_label','n2n_label','n1n_label'):
            if lab in self.ids:
                self.ids[lab].text = ""
        # set details to '-'
        for lab in (
            'n2f_mission','n2f_vehicle','n2f_spacecraft','n2f_arrival','n2f_departure',
            'n2z_mission','n2z_vehicle','n2z_spacecraft','n2z_arrival','n2z_departure',
            'n2n_mission','n2n_vehicle','n2n_spacecraft','n2n_arrival','n2n_departure',
            'n1n_mission','n1n_vehicle','n1n_spacecraft','n1n_arrival','n1n_departure',
        ):
            if lab in self.ids:
                self.ids[lab].text = "-"
        for icon in ('n2f_dragon','n2f_starliner','n2z_dragon','n2z_starliner','n1n_cygnus','n2n_cygnus'):
            if icon in self.ids:
                self.ids[icon].opacity = 0.0
