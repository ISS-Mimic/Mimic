from __future__ import annotations
from kivy.uix.screenmanager import Screen
import pathlib
from kivy.lang import Builder
from kivy.clock import Clock
from utils.logger import log_info, log_error
import sqlite3
from pathlib import Path
import math
from ._base import MimicBase

kv_path = pathlib.Path(__file__).with_name("GNC_Screen.kv")
Builder.load_file(str(kv_path))

class GNC_Screen(MimicBase):
    """Guidance, Navigation and Control (GNC) summary: attitude, CMGs."""

    _update_event = None

    def on_enter(self):
        try:
            self.update_gnc_values(0)
            self._update_event = Clock.schedule_interval(self.update_gnc_values, 2)
            log_info("GNC: started updates (2s)")
        except Exception as exc:
            log_error(f"GNC on_enter failed: {exc}")

    def on_leave(self):
        try:
            if self._update_event is not None:
                Clock.unschedule(self._update_event)
                self._update_event = None
                log_info("GNC: stopped updates")
        except Exception as exc:
            log_error(f"GNC on_leave failed: {exc}")

    def _get_db_path(self) -> Path:
        shm = Path('/dev/shm/iss_telemetry.db')
        if shm.exists():
            return shm
        return Path.home() / '.mimic_data' / 'iss_telemetry.db'

    def update_gnc_values(self, _dt):
        try:
            db_path = self._get_db_path()
            if not db_path.exists():
                return
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute('select Value from telemetry')
            values = cur.fetchall()
            conn.close()

            # Errors
            rollerror = float(values[165][0])
            pitcherror = float(values[166][0])
            yawerror = float(values[167][0])

            # Quaternion q0..q3
            q0 = float(values[171][0])
            q1 = float(values[172][0])
            q2 = float(values[173][0])
            q3 = float(values[174][0])

            # Compute Euler angles (deg) with bounds and errors
            roll = math.degrees(math.atan2(2.0 * (q0 * q1 + q2 * q3), 1.0 - 2.0 * (q1 * q1 + q2 * q2))) + rollerror
            pitch = math.degrees(math.asin(max(-1.0, min(1.0, 2.0 * (q0 * q2 - q3 * q1))))) + pitcherror
            yaw = math.degrees(math.atan2(2.0 * (q0 * q3 + q1 * q2), 1.0 - 2.0 * (q2 * q2 + q3 * q3))) + yawerror

            if 'yaw' in self.ids:
                self.ids.yaw.text = f"{yaw:.2f}"
            if 'pitch' in self.ids:
                self.ids.pitch.text = f"{pitch:.2f}"
            if 'roll' in self.ids:
                self.ids.roll.text = f"{roll:.2f}"

            # CMG momentum saturation
            try:
                cmg_mom_percent = float(values[154][0])
                if 'cmgsaturation' in self.ids:
                    self.ids.cmgsaturation.value = cmg_mom_percent
                if 'cmgsaturation_value' in self.ids:
                    self.ids.cmgsaturation_value.text = f"CMG Saturation {cmg_mom_percent:.1f}%"
            except Exception:
                pass

            # CMG activity flags → image selection
            # 1=active → cmg.png else cmg_offline.png
            cmg_active = {}
            try:
                cmg_active[1] = int(values[145][0])
                cmg_active[2] = int(values[146][0])
                cmg_active[3] = int(values[147][0])
                cmg_active[4] = int(values[148][0])
            except Exception:
                pass
            base = f"{self.mimic_directory}/Mimic/Pi/imgs/gnc"
            for i in (1, 2, 3, 4):
                img_id = f"cmg{i}"
                if img_id in self.ids:
                    try:
                        self.ids[img_id].source = f"{base}/cmg.png" if cmg_active.get(i, 0) == 1 else f"{base}/cmg_offline.png"
                    except Exception:
                        pass

            # Per-CMG telemetry
            def set_text(id_name: str, fmt: str, value_idx: int, decimals: int = 1):
                if id_name in self.ids:
                    try:
                        val = float(values[value_idx][0])
                        self.ids[id_name].text = f"{fmt} {val:.{decimals}f}"
                    except Exception:
                        self.ids[id_name].text = 'n/a'

            set_text('cmg1spintemp', 'Spin Temp', 181, 1)
            set_text('cmg1halltemp', 'Hall Temp', 185, 1)
            set_text('cmg1vibration', 'Vibration', 237, 4)
            set_text('cmg1current', 'Current', 241, 1)
            set_text('cmg1speed', 'Speed', 245, 1)

            set_text('cmg2spintemp', 'Spin Temp', 182, 1)
            set_text('cmg2halltemp', 'Hall Temp', 186, 1)
            set_text('cmg2vibration', 'Vibration', 238, 4)
            set_text('cmg2current', 'Current', 242, 1)
            set_text('cmg2speed', 'Speed', 246, 1)

            set_text('cmg3spintemp', 'Spin Temp', 183, 1)
            set_text('cmg3halltemp', 'Hall Temp', 187, 1)
            set_text('cmg3vibration', 'Vibration', 239, 4)
            set_text('cmg3current', 'Current', 243, 1)
            set_text('cmg3speed', 'Speed', 247, 1)

            set_text('cmg4spintemp', 'Spin Temp', 184, 1)
            set_text('cmg4halltemp', 'Hall Temp', 188, 1)
            set_text('cmg4vibration', 'Vibration', 240, 4)
            set_text('cmg4current', 'Current', 244, 1)
            set_text('cmg4speed', 'Speed', 248, 1)

        except Exception as exc:
            log_error(f"GNC update failed: {exc}")
