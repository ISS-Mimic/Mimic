from __future__ import annotations
from kivy.uix.screenmanager import Screen
import pathlib
from kivy.lang import Builder
from kivy.clock import Clock
from utils.logger import log_info, log_error
import sqlite3
from pathlib import Path
from ._base import MimicBase

kv_path = pathlib.Path(__file__).with_name("Robo_Screen.kv")
Builder.load_file(str(kv_path))

class Robo_Screen(MimicBase):
    """Robotics summary: SSRMS base, location; MT worksite; SPDM base states."""

    _update_event = None

    def on_enter(self):
        try:
            self.update_robo_values(0)
            self._update_event = Clock.schedule_interval(self.update_robo_values, 2)
            log_info("ROBO: started updates (2s)")
        except Exception as exc:
            log_error(f"ROBO on_enter failed: {exc}")

    def on_leave(self):
        try:
            if self._update_event is not None:
                Clock.unschedule(self._update_event)
                self._update_event = None
                log_info("ROBO: stopped updates")
        except Exception as exc:
            log_error(f"ROBO on_leave failed: {exc}")

    def _get_db_path(self) -> Path:
        shm = Path('/dev/shm/iss_telemetry.db')
        if shm.exists():
            return shm
        return Path.home() / '.mimic_data' / 'iss_telemetry.db'

    def update_robo_values(self, _dt):
        try:
            db_path = self._get_db_path()
            if not db_path.exists():
                return
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute('select Value from telemetry')
            values = cur.fetchall()
            conn.close()

            # MT worksite (values[258])
            try:
                mt_worksite = int(float(values[258][0]))
                if 'mt_worksite' in self.ids:
                    self.ids.mt_worksite.text = str(mt_worksite)
            except Exception:
                if 'mt_worksite' in self.ids:
                    self.ids.mt_worksite.text = 'n/a'

            # SSRMS Operating Base (values[261]): 0 -> A, 5 -> B
            try:
                operating_base = int(float(values[261][0]))
                if 'OperatingBase' in self.ids:
                    if operating_base == 0:
                        self.ids.OperatingBase.text = 'LEE A'
                    elif operating_base == 5:
                        self.ids.OperatingBase.text = 'LEE B'
                    else:
                        self.ids.OperatingBase.text = 'n/a'
            except Exception:
                if 'OperatingBase' in self.ids:
                    self.ids.OperatingBase.text = 'n/a'

            # SSRMS Base Location (values[260])
            try:
                base_location = int(float(values[260][0]))
                base_map = {
                    1: 'Lab',
                    2: 'Node 3',
                    4: 'Node 2',
                    7: 'MBS PDGF 1',
                    8: 'MBS PDGF 2',
                    11: 'MBS PDGF 3',
                    13: 'MBS PDGF 4',
                    14: 'FGB',
                    16: 'POA',
                    19: 'SSRMS Tip LEE',
                    63: 'Undefined',
                }
                if 'BaseLocation' in self.ids:
                    self.ids.BaseLocation.text = base_map.get(base_location, 'n/a')
            except Exception:
                if 'BaseLocation' in self.ids:
                    self.ids.BaseLocation.text = 'n/a'

            # SPDM Base (values[271])
            try:
                spdm_base = int(float(values[271][0]))
                spdm_base_map = {
                    1: 'Lab',
                    2: 'Node 3',
                    4: 'Node 2',
                    7: 'MBS PDGF 1',
                    8: 'MBS PDGF 2',
                    11: 'MBS PDGF 3',
                    13: 'MBS PDGF 4',
                    14: 'FGB',
                    16: 'POA',
                    19: 'SSRMS Tip LEE',
                    63: 'Undefined',
                }
                if 'SPDMbase' in self.ids:
                    self.ids.SPDMbase.text = spdm_base_map.get(spdm_base, 'n/a')
            except Exception:
                if 'SPDMbase' in self.ids:
                    self.ids.SPDMbase.text = 'n/a'

            # SPDM Operating Base (packed values[270], bits 8..11)
            try:
                packed_spdm0001 = int(float(values[270][0]))
                oper_field = (packed_spdm0001 >> 8) & 0xF
                oper_map = {1: 'SPDM Body LEE', 2: 'SPDM Body PDGF'}
                if 'SPDMoperatingBase' in self.ids:
                    self.ids.SPDMoperatingBase.text = oper_map.get(oper_field, 'n/a')
            except Exception:
                if 'SPDMoperatingBase' in self.ids:
                    self.ids.SPDMoperatingBase.text = 'n/a'

        except Exception as exc:
            log_error(f"ROBO update failed: {exc}")
