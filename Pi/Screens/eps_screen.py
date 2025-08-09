from __future__ import annotations
from kivy.uix.screenmanager import Screen
import pathlib
from kivy.lang import Builder
from kivy.clock import Clock
from utils.logger import log_info, log_error
import sqlite3
from pathlib import Path
from ._base import MimicBase

kv_path = pathlib.Path(__file__).with_name("EPS_Screen.kv")
Builder.load_file(str(kv_path))

class EPS_Screen(MimicBase):
    """EPS summary: SARJs, beta angles, per-array V/I, USOS power, sun indicator."""

    _update_event = None
    _eps_index: int = 0
    _v_buffers: dict[str, list[float]] | None = None

    def on_enter(self):
        try:
            # initialize smoothing buffers (10-sample history per channel)
            self._v_buffers = {
                '1a': [154.1] * 10,
                '1b': [154.1] * 10,
                '2a': [154.1] * 10,
                '2b': [154.1] * 10,
                '3a': [154.1] * 10,
                '3b': [154.1] * 10,
                '4a': [154.1] * 10,
                '4b': [154.1] * 10,
            }
            self._eps_index = 0
            self.update_eps_values(0)
            self._update_event = Clock.schedule_interval(self.update_eps_values, 2)
            log_info("EPS: started updates (2s)")
        except Exception as exc:
            log_error(f"EPS on_enter failed: {exc}")

    def on_leave(self):
        try:
            if self._update_event is not None:
                Clock.unschedule(self._update_event)
                self._update_event = None
                log_info("EPS: stopped updates")
        except Exception as exc:
            log_error(f"EPS on_leave failed: {exc}")

    def _get_db_path(self) -> Path:
        shm = Path('/dev/shm/iss_telemetry.db')
        if shm.exists():
            return shm
        return Path.home() / '.mimic_data' / 'iss_telemetry.db'

    def _set_text(self, id_name: str, text: str):
        if id_name in self.ids:
            self.ids[id_name].text = text

    def update_eps_values(self, _dt):
        try:
            db_path = self._get_db_path()
            if not db_path.exists():
                return
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute('select Value from telemetry')
            values = cur.fetchall()
            conn.close()

            # SARJs and betas
            psarj = float(values[0][0])
            ssarj = float(values[1][0])
            beta1b = float(values[4][0])
            beta1a = float(values[5][0])
            beta2b = float(values[6][0])
            beta2a = float(values[7][0])
            beta3b = float(values[8][0])
            beta3a = float(values[9][0])
            beta4b = float(values[10][0])
            beta4a = float(values[11][0])

            self._set_text('beta1b_value', f"{beta1b:.2f}")
            self._set_text('beta1a_value', f"{beta1a:.2f}")
            self._set_text('beta2b_value', f"{beta2b:.2f}")
            self._set_text('beta2a_value', f"{beta2a:.2f}")
            self._set_text('beta3b_value', f"{beta3b:.2f}")
            self._set_text('beta3a_value', f"{beta3a:.2f}")
            self._set_text('beta4b_value', f"{beta4b:.2f}")
            self._set_text('beta4a_value', f"{beta4a:.2f}")

            # Per-array V/I
            v = { '1a': float(values[25][0]), '1b': float(values[26][0]), '2a': float(values[27][0]), '2b': float(values[28][0]), '3a': float(values[29][0]), '3b': float(values[30][0]), '4a': float(values[31][0]), '4b': float(values[32][0]) }
            c = { '1a': float(values[33][0]), '1b': float(values[34][0]), '2a': float(values[35][0]), '2b': float(values[36][0]), '3a': float(values[37][0]), '3b': float(values[38][0]), '4a': float(values[39][0]), '4b': float(values[40][0]) }
            for key in ('1a','1b','2a','2b','3a','3b','4a','4b'):
                self._set_text(f"v{key}_value", f"{v[key]:.2f}V")
                self._set_text(f"c{key}_value", f"{c[key]:.2f}A")

            # Smooth the array state with 10-sample averaging and update imagery
            if self._v_buffers is not None:
                idx = self._eps_index % 10
                for key in v.keys():
                    self._v_buffers[key][idx] = v[key]

                def avg(vals: list[float]) -> float:
                    return sum(vals) / len(vals) if vals else 0.0

                base_path = f"{self.mimic_directory}/Mimic/Pi/imgs/eps"

                def set_array_image(arr_key: str, widget_id: str):
                    try:
                        v_avg = avg(self._v_buffers[arr_key])
                        current = c[arr_key]
                        # Default by averaged voltage
                        if v_avg < 151.5:
                            src = f"{base_path}/array-discharging.zip"
                        elif v_avg > 160.0:
                            src = f"{base_path}/array-charged.zip"
                        else:
                            src = f"{base_path}/array-charging.zip"
                        # Offline override if current positive
                        if current > 0.0:
                            src = f"{base_path}/array-offline.png"
                        if widget_id in self.ids:
                            self.ids[widget_id].source = src
                    except Exception:
                        pass

                set_array_image('1a', 'array_1a')
                set_array_image('1b', 'array_1b')
                set_array_image('2a', 'array_2a')
                set_array_image('2b', 'array_2b')
                set_array_image('3a', 'array_3a')
                set_array_image('3b', 'array_3b')
                set_array_image('4a', 'array_4a')
                set_array_image('4b', 'array_4b')

                self._eps_index = (self._eps_index + 1) % 10

            # USOS Power sum
            usos_power = sum(v[k] * c[k] for k in v.keys())
            self._set_text('usos_power', f"{usos_power*-1.0:.0f} W")

            # Sun icon visibility: any channel voltage >= 151.5
            try:
                any_sun = any(vv >= 151.5 for vv in v.values())
                if 'eps_sun' in self.ids:
                    self.ids.eps_sun.color = (1,1,1,1) if any_sun else (1,1,1,0.1)
            except Exception:
                pass

            # Solar beta label
            try:
                solarbeta = float(values[176][0])
                self._set_text('solarbeta', f"{solarbeta:.2f}")
            except Exception:
                pass

            # Show SARJs (deg)
            self._set_text('psarj_value', f"{psarj:.2f}deg")
            self._set_text('ssarj_value', f"{ssarj:.2f}deg")

        except Exception as exc:
            log_error(f"EPS update failed: {exc}")
