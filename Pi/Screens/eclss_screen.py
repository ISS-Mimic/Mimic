from __future__ import annotations
from kivy.uix.screenmanager import Screen
import pathlib
from kivy.lang import Builder
from kivy.clock import Clock
from utils.logger import log_info, log_error
import sqlite3
from pathlib import Path
from ._base import MimicBase

kv_path = pathlib.Path(__file__).with_name("ECLSS_Screen.kv")
Builder.load_file(str(kv_path))

class ECLSS_Screen(MimicBase):
    """ECLSS summary: cabin/airlock pressures, water levels, O2 generator state, valves."""

    _update_event = None

    def on_enter(self):
        try:
            self.update_eclss_values(0)
            self._update_event = Clock.schedule_interval(self.update_eclss_values, 2)
            log_info("ECLSS: started updates (2s)")
        except Exception as exc:
            log_error(f"ECLSS on_enter failed: {exc}")

    def on_leave(self):
        try:
            if self._update_event is not None:
                Clock.unschedule(self._update_event)
                self._update_event = None
                log_info("ECLSS: stopped updates")
        except Exception as exc:
            log_error(f"ECLSS on_leave failed: {exc}")

    def _get_db_path(self) -> Path:
        shm = Path('/dev/shm/iss_telemetry.db')
        if shm.exists():
            return shm
        return Path.home() / '.mimic_data' / 'iss_telemetry.db'

    def update_eclss_values(self, _dt):
        try:
            db_path = self._get_db_path()
            if not db_path.exists():
                return
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute('select Value from telemetry')
            values = cur.fetchall()
            conn.close()

            def set_text(id_name: str, text: str):
                if id_name in self.ids:
                    self.ids[id_name].text = text

            # Scalars
            set_text('CabinTemp', f"{float(values[195][0]):.2f}")
            set_text('CabinPress', f"{float(values[194][0]):.2f}")
            set_text('CrewlockPress', f"{float(values[16][0]):.2f}")
            set_text('AirlockPress', f"{float(values[77][0]):.2f}")
            set_text('CleanWater', f"{float(values[93][0]):.2f}")
            set_text('WasteWater', f"{float(values[94][0]):.2f}")
            set_text('O2prodRate', f"{float(values[96][0]):.2f}")

            # O2gen state mapping
            try:
                O2genState = int(float(values[95][0]))
                o2_map = {
                    1: 'PROCESS',
                    2: 'STANDBY',
                    3: 'SHUTDOWN',
                    4: 'STOP',
                    5: 'VENT DOME',
                    6: 'INERT DOME',
                    7: 'FAST SHTDWN',
                    8: 'N2 PURGE SHTDWN',
                }
                set_text('O2genState', o2_map.get(O2genState, 'n/a'))
            except Exception:
                set_text('O2genState', 'n/a')

            # Valve positions
            try:
                VRSvlvPosition = int(float(values[199][0]))
                vmap = {0: 'FAIL', 1: 'OPEN', 2: 'CLSD', 3: 'TRNS'}
                set_text('VRSvlvPosition', vmap.get(VRSvlvPosition, 'n/a'))
            except Exception:
                set_text('VRSvlvPosition', 'n/a')
            try:
                VESvlvPosition = int(float(values[198][0]))
                vmap = {0: 'FAIL', 1: 'OPEN', 2: 'CLSD', 3: 'TRNS'}
                set_text('VESvlvPosition', vmap.get(VESvlvPosition, 'n/a'))
            except Exception:
                set_text('VESvlvPosition', 'n/a')

        except Exception as exc:
            log_error(f"ECLSS update failed: {exc}")
