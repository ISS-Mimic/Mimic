from __future__ import annotations
from kivy.uix.screenmanager import Screen
import pathlib
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty
from utils.logger import log_info, log_error
import sqlite3
from pathlib import Path
from ._base import MimicBase

class MTSpeedometer(Widget):
    """Simple needle gauge for MT speed (cm/s)."""
    speed_cms = NumericProperty(0.0)
    min_speed = NumericProperty(0.0)
    max_speed = NumericProperty(5.5)
    start_angle = NumericProperty(-120.0)
    end_angle = NumericProperty(120.0)

class MSS_MT_Screen(MimicBase):
    """Mobile Transporter (MT) status screen: worksite, position, speed, payloads."""

    _update_event = None
    _prev_timestamp: float | None = None
    _prev_position: float | None = None
    _last_speed_cms: float = 0.0

    def on_enter(self):
        try:
            self.update_mt_values(0)
            self._update_event = Clock.schedule_interval(self.update_mt_values, 2)
            log_info("MSS/MT: started updates (2s)")
        except Exception as exc:
            log_error(f"MSS/MT on_enter failed: {exc}")

    def on_leave(self):
        try:
            if self._update_event is not None:
                Clock.unschedule(self._update_event)
                self._update_event = None
                log_info("MSS/MT: stopped updates")
        except Exception as exc:
            log_error(f"MSS/MT on_leave failed: {exc}")

    def _get_db_path(self) -> Path:
        shm = Path('/dev/shm/iss_telemetry.db')
        if shm.exists():
            return shm
        return Path.home() / '.mimic_data' / 'iss_telemetry.db'

    def _map_mt_center_x(self, mt_position_value: float) -> float:
        """Map raw MT position to screen x percentage for `FloatingMT.center_x`.

        Uses placeholder min/max; adjust with real calibration when available.
        """
        mt_min_value = 2000.0  # TODO: calibrate
        mt_max_value = -2000.0  # TODO: calibrate
        min_mt_mapped_value = 0.4
        max_mt_mapped_value = 0.9

        # avoid division by zero
        if mt_max_value == mt_min_value:
            return (min_mt_mapped_value + max_mt_mapped_value) / 2.0

        ratio = (mt_position_value - mt_min_value) / (mt_max_value - mt_min_value)
        return min_mt_mapped_value + ratio * (max_mt_mapped_value - min_mt_mapped_value)

    def update_mt_values(self, _dt):
        try:
            db_path = self._get_db_path()
            if not db_path.exists():
                return

            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute('select Value from telemetry')
            values = cur.fetchall()
            cur.execute('select Timestamp from telemetry')
            timestamps = cur.fetchall()
            conn.close()

            # Worksite (values[258])
            try:
                mt_worksite = int(float(values[258][0]))
                if 'mt_ws_value' in self.ids:
                    self.ids.mt_ws_value.text = str(mt_worksite)
            except Exception:
                if 'mt_ws_value' in self.ids:
                    self.ids.mt_ws_value.text = 'n/a'

            # Position (values[257]) and timestamp
            try:
                mt_position = float(values[257][0])
                mt_position_timestamp = float(timestamps[257][0])
                if 'mt_position_value' in self.ids:
                    self.ids.mt_position_value.text = f"{mt_position}"
                # Update FloatingMT position
                if 'FloatingMT' in self.ids:
                    self.ids.FloatingMT.pos_hint = {
                        'center_x': self._map_mt_center_x(mt_position),
                        'center_y': 0.375,
                    }
                # Speed (cm/s) estimation using prior sample
                if self._prev_timestamp is not None and mt_position_timestamp > self._prev_timestamp:
                    delta_pos = mt_position - (self._prev_position or 0.0)
                    delta_t_hours = (mt_position_timestamp - self._prev_timestamp) * 3600.0
                    if delta_t_hours != 0:
                        self._last_speed_cms = delta_pos / delta_t_hours
                self._prev_timestamp = mt_position_timestamp
                self._prev_position = mt_position
            except Exception:
                pass

            # Speed label
            if 'mt_speed_value' in self.ids:
                try:
                    self.ids.mt_speed_value.text = f"{self._last_speed_cms:0.2f} cm/s"
                except Exception:
                    self.ids.mt_speed_value.text = 'n/a'
            # Update speedometer widget if present
            if 'mt_speedometer' in self.ids:
                try:
                    self.ids.mt_speedometer.speed_cms = float(self._last_speed_cms)
                except Exception:
                    self.ids.mt_speedometer.speed_cms = 0.0


            # Payload labels with state mapping
            try:
                if 'MCASpayload' in self.ids:
                    mcas_val = int(float(values[293][0]))
                    if mcas_val == 0:
                        self.ids.MCASpayload.text = 'Released'
                    elif mcas_val == 1:
                        self.ids.MCASpayload.text = 'Captured'
                    else:
                        self.ids.MCASpayload.text = 'n/a'
            except Exception:
                if 'MCASpayload' in self.ids:
                    self.ids.MCASpayload.text = 'n/a'
            try:
                if 'POApayload' in self.ids:
                    poa_val = int(float(values[294][0]))
                    if poa_val == 0:
                        self.ids.POApayload.text = 'Released'
                    elif poa_val == 1:
                        self.ids.POApayload.text = 'Captive'
                    elif poa_val == 2:
                        self.ids.POApayload.text = 'Captured'
                    else:
                        self.ids.POApayload.text = 'n/a'
            except Exception:
                if 'POApayload' in self.ids:
                    self.ids.POApayload.text = 'n/a'

            # need to unpack the values for POA and MCAS
            # CSAMBA00003 = values[295]
            try:
                packed_csamaba00003 = int(float(values[295][0]))
                # POA Stop, Speed, Hot
                poa_stop = (packed_csamaba00003 >> 14) & 0x3
                poa_speed = (packed_csamaba00003 >> 12) & 0x3
                poa_hot = (packed_csamaba00003 >> 11) & 0x1
                stop_map = {1: 'Soft Stop', 2: 'Hard Stop'}
                speed_map = {1: 'Slow', 2: 'Fast'}
                hot_map = {0: 'Null', 1: 'Hot'}
                if 'POA_Stop_Condition' in self.ids:
                    self.ids.POA_Stop_Condition.text = stop_map.get(poa_stop, 'n/a')
                if 'POA_Run_Speed' in self.ids:
                    self.ids.POA_Run_Speed.text = speed_map.get(poa_speed, 'n/a')
                if 'POA_Hot' in self.ids:
                    self.ids.POA_Hot.text = hot_map.get(poa_hot, 'n/a')
            except Exception:
                if 'POA_Stop_Condition' in self.ids:
                    self.ids.POA_Stop_Condition.text = 'n/a'
                if 'POA_Run_Speed' in self.ids:
                    self.ids.POA_Run_Speed.text = 'n/a'
                if 'POA_Hot' in self.ids:
                    self.ids.POA_Hot.text = 'n/a'

            # CSAMBS00001 (values[292]): MBS Operating Base and Base Location
            try:
                packed_csambs00001 = int(float(values[292][0]))
                mbs_op_base = (packed_csambs00001 >> 8) & 0xF
                mbs_loc = packed_csambs00001 & 0x3F
                op_map = {3: 'MTCL', 4: 'TUS'}
                loc_map = {58: 'MT', 60: 'TUS', 63: 'Undefined'}
                if 'MBS_Operating_Base' in self.ids:
                    self.ids.MBS_Operating_Base.text = op_map.get(mbs_op_base, 'n/a')
                if 'MBS_Base_Location' in self.ids:
                    self.ids.MBS_Base_Location.text = loc_map.get(mbs_loc, 'n/a')
            except Exception:
                if 'MBS_Operating_Base' in self.ids:
                    self.ids.MBS_Operating_Base.text = 'n/a'
                if 'MBS_Base_Location' in self.ids:
                    self.ids.MBS_Base_Location.text = 'n/a'

            
        except Exception as exc:
            log_error(f"MSS/MT update failed: {exc}")


# Load KV after classes are defined so custom widgets are available
kv_path = pathlib.Path(__file__).with_name("MSS_MT_Screen.kv")
Builder.load_file(str(kv_path))
