from __future__ import annotations
from kivy.uix.screenmanager import Screen
import pathlib
from kivy.lang import Builder
from kivy.clock import Clock
from utils.logger import log_info, log_error
import sqlite3
from pathlib import Path
from ._base import MimicBase

kv_path = pathlib.Path(__file__).with_name("SPDM_Screen.kv")
Builder.load_file(str(kv_path))

class SPDM_Screen(MimicBase):
    """SPDM (Dextre) status: bases, OTCMs, and 2x7 DOF joint angles."""

    _update_event = None

    def on_enter(self):
        try:
            self.update_spdm_values(0)
            self._update_event = Clock.schedule_interval(self.update_spdm_values, 2)
            log_info("SPDM: started updates (2s)")
        except Exception as exc:
            log_error(f"SPDM on_enter failed: {exc}")

    def on_leave(self):
        try:
            if self._update_event is not None:
                Clock.unschedule(self._update_event)
                self._update_event = None
                log_info("SPDM: stopped updates")
        except Exception as exc:
            log_error(f"SPDM on_leave failed: {exc}")

    def _get_db_path(self) -> Path:
        shm = Path('/dev/shm/iss_telemetry.db')
        if shm.exists():
            return shm
        return Path.home() / '.mimic_data' / 'iss_telemetry.db'

    def _fmt2(self, v):
        try:
            return f"{float(v):.2f}"
        except Exception:
            return str(v)

    def _set_text(self, id_name: str, text: str):
        if id_name in self.ids:
            self.ids[id_name].text = text

    def _set_angle(self, id_name: str, values, idx: int):
        try:
            self._set_text(id_name, f"{float(values[idx][0]):.2f} deg")
        except Exception:
            pass

    def update_spdm_values(self, _dt):
        try:
            db_path = self._get_db_path()
            if not db_path.exists():
                return
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute('select Value from telemetry')
            values = cur.fetchall()
            conn.close()

            # Bases
            spdm_base_idx = 271
            spdm_oper_base_idx = 270
            try:
                SPDMbase = int(float(values[spdm_base_idx][0]))
                base_map = {
                    1: "Lab",
                    2: "Node 3",
                    4: "Node 2",
                    7: "MBS PDGF 1",
                    8: "MBS PDGF 2",
                    11: "MBS PDGF 3",
                    13: "MBS PDGF 4",
                    14: "FGB",
                    16: "POA",
                    19: "SSRMS Tip LEE",
                    63: "Undefined",
                }
                self._set_text('SPDMbase', base_map.get(SPDMbase, 'n/a'))
            except Exception:
                self._set_text('SPDMbase', 'n/a')

            try:
                # CSASPDM0001 packed: SPDM operating base in bits 8..11
                packed_spdm0001 = int(float(values[spdm_oper_base_idx][0]))
                oper_field = (packed_spdm0001 >> 8) & 0xF
                oper_map = {1: 'SPDM Body LEE', 2: 'SPDM Body PDGF'}
                self._set_text('SPDMoperatingBase', oper_map.get(oper_field, 'n/a'))
            except Exception:
                self._set_text('SPDMoperatingBase', 'n/a')

            # OTCM / payload statuses
            try:
                Arm1OTCM = int(float(values[279][0]))
                status_map = {0: 'Released', 1: 'Captive', 2: 'Captured'}
                self._set_text('Arm1OTCM', status_map.get(Arm1OTCM, 'n/a'))
            except Exception:
                self._set_text('Arm1OTCM', 'n/a')

            try:
                Arm2OTCM = int(float(values[288][0]))
                status_map = {0: 'Released', 1: 'Captive', 2: 'Captured'}
                self._set_text('Arm2OTCM', status_map.get(Arm2OTCM, 'n/a'))
            except Exception:
                self._set_text('Arm2OTCM', 'n/a')

            try:
                BodyPayload = int(float(values[288][0]))
                status_map = {0: 'Released', 1: 'Captive', 2: 'Captured'}
                self._set_text('BodyPayload', status_map.get(BodyPayload, 'n/a'))
            except Exception:
                self._set_text('BodyPayload', 'n/a')

            # Angles – Arm 1
            self._set_angle('Shoulder1Roll', values, 272)
            self._set_angle('Shoulder1Yaw', values, 273)
            self._set_angle('Shoulder1Pitch', values, 274)
            self._set_angle('Elbow1Pitch', values, 275)
            self._set_angle('Wrist1Roll', values, 276)
            self._set_angle('Wrist1Yaw', values, 277)
            self._set_angle('Wrist1Pitch', values, 278)

            # Angles – Arm 2 (indices inferred; guard each)
            self._set_angle('Shoulder2Roll', values, 280)
            self._set_angle('Shoulder2Yaw', values, 281)
            self._set_angle('Shoulder2Pitch', values, 282)
            self._set_angle('Elbow2Pitch', values, 283)
            self._set_angle('Wrist2Roll', values, 285)
            self._set_angle('Wrist2Yaw', values, 286)
            self._set_angle('Wrist2Pitch', values, 284)

            # Body roll
            self._set_angle('BodyRoll', values, 289)

            # -------- Bitfield decodes (IDs may not exist yet; set only if present)
            # CSASPDM0021 (index 290): SPDM LEE Stop/Speed/Hot
            try:
                packed_spdm0021 = int(float(values[290][0]))
                lee_stop = (packed_spdm0021 >> 6) & 0x3
                lee_speed = (packed_spdm0021 >> 4) & 0x3
                lee_hot = (packed_spdm0021 >> 3) & 0x1
                stop_map = {1: 'Soft Stop', 2: 'Hard Stop'}
                speed_map = {1: 'Slow', 2: 'Fast'}
                hot_map = {0: 'Null', 1: 'Hot'}
                if 'SPDM_LEE_Stop_Condition' in self.ids:
                    self.ids.SPDM_LEE_Stop_Condition.text = stop_map.get(lee_stop, 'n/a')
                if 'SPDM_LEE_Run_Speed' in self.ids:
                    self.ids.SPDM_LEE_Run_Speed.text = speed_map.get(lee_speed, 'n/a')
                if 'SPDM_LEE_Hot' in self.ids:
                    self.ids.SPDM_LEE_Hot.text = hot_map.get(lee_hot, 'n/a')
            except Exception:
                pass

            # CSASPDM0018 (index 287): Arm1 Hot (bit3), Arm2 Hot (bit11)
            try:
                packed_spdm0018 = int(float(values[287][0]))
                arm1_hot = (packed_spdm0018 >> 3) & 0x1
                arm2_hot = (packed_spdm0018 >> 11) & 0x1
                hot_map = {0: 'Null', 1: 'Hot'}
                if 'SPDM_Arm1_Hot' in self.ids:
                    self.ids.SPDM_Arm1_Hot.text = hot_map.get(arm1_hot, 'n/a')
                if 'SPDM_Arm2_Hot' in self.ids:
                    self.ids.SPDM_Arm2_Hot.text = hot_map.get(arm2_hot, 'n/a')
            except Exception:
                pass

        except Exception as exc:
            log_error(f"SPDM update failed: {exc}")
