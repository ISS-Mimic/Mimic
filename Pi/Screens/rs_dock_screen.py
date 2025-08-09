from __future__ import annotations

import pathlib, logging, sqlite3
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.clock import Clock

from ._base import MimicBase                        # common mimic_directory / signalcolor
from utils.logger import log_info, log_error

kv_path = pathlib.Path(__file__).with_name("RS_Dock_Screen.kv")
Builder.load_file(str(kv_path))

class RS_Dock_Screen(MimicBase):
    """
    R-S docking status bar that resizes whenever the window changes.
    """

    # signalcolor already comes from MimicBase

    docking_bar      = ObjectProperty(None)   # filled by ids in KV
    dock_layout      = ObjectProperty(None)

    # ------------------------------------------------------------------ init
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(on_resize=self.update_docking_bar)
        self.bind(size=self.update_docking_bar, pos=self.update_docking_bar)
        Clock.schedule_once(self.update_docking_bar, 0)
        self._telemetry_event = None
        from collections import deque
        self._range_samples = deque(maxlen=10)

    # ---------------------------------------------------------------- layout
    def update_docking_bar(self, *_):
        width, height = Window.size
        bar = self.ids.docking_bar

        bar.size       = (width * 0.325, height * 0.04)   # narrower bar
        bar.pos        = (width * 0.53,  height * 0.205)  # position under ISS
        bar.size_hint  = (None, None)                     # ignore layout hints

        self.ids.dock_layout.do_layout()

    def update_docking_bar_width(self, value: float):
        """
        Map incoming telemetry value (0-80 000) to a 0-1 range,
        invert, and shrink the bar width accordingly.
        """
        try:
            width, _ = Window.size
            mapped = max(0.0, 1 - float(value) / 80_000)
            new_w  = width * 0.325 * mapped
            self.ids.docking_bar.size = (new_w, self.ids.docking_bar.height)
            self.ids.dock_layout.do_layout()
        except Exception as exc:
            log_error(f"update_docking_bar_width failed: {exc}")

    # ------------------------------------------------------------------- live
    def on_enter(self):
        try:
            self._telemetry_event = Clock.schedule_interval(self._update_from_db, 1)
        except Exception as exc:
            log_error(f"RS_Dock on_enter failed: {exc}")

    def on_leave(self):
        try:
            if self._telemetry_event is not None:
                Clock.unschedule(self._telemetry_event)
                self._telemetry_event = None
        except Exception as exc:
            log_error(f"RS_Dock on_leave failed: {exc}")

    def _get_db_path(self) -> pathlib.Path:
        shm = pathlib.Path('/dev/shm/iss_telemetry.db')
        if shm.exists():
            return shm
        return pathlib.Path.home() / '.mimic_data' / 'iss_telemetry.db'

    def _fetch_values(self):
        db_path = self._get_db_path()
        if not db_path.exists():
            return None, None
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        cur.execute('select Value from telemetry')
        values = cur.fetchall()
        cur.execute('select Timestamp from telemetry')
        timestamps = cur.fetchall()
        conn.close()
        return values, timestamps

    def _update_from_db(self, _dt):
        """Query telemetry DB directly and update RS Dock UI."""
        try:
            values, timestamps = self._fetch_values()
            if not values:
                return

            # Mappings from GUI.py
            ros_mode_texts = {
                1.0: "Crew Rescue",
                2.0: "Survival",
                3.0: "Reboost",
                4.0: "Proximity Operations",
                5.0: "EVA",
                6.0: "Microgravity",
                7.0: "Standard",
            }
            rs_att_mode_texts = {
                0.0: "Inertial",
                1.0: "LVLH SM",
                2.0: "Solar Orientation",
                3.0: "Current LVLH",
                4.0: "Current Inertial Attitude",
                5.0: "Damping",
                6.0: "TEA",
                7.0: "X-POP",
            }
            rs_motion_control_texts = {0.0: "Undetermined State", 1.0: "RS Master"}
            rs_prep_free_drift_texts = {0.0: "Undetermined State", 1.0: "Prepared to Free Drift"}
            rs_thruster_operation_texts = {0.0: "Pre-Starting Procedure", 1.0: "Thruster Operation Terminated"}
            rs_current_dynamic_texts = {
                0.0: "Reserve",
                1.0: "Thrusters",
                2.0: "Gyrodines",
                3.0: "Gyrodines Desat (US Method)",
                4.0: "Gyrodines Desat (RS Method)",
                5.0: "Translational Thrusters",
                6.0: "Thrusters help CMG",
                7.0: "Free Drift",
            }
            rs_docking_port_texts = {0.0: "Undetermined State", 1.0: "Docking Port Engaged"}
            rs_vv_docking_port_texts = {0.0: "Undetermined State", 1.0: "Soyuz/Progress Docked"}
            rs_signal_texts = {0.0: "Undetermined State", 1.0: "Yes"}
            rs_hooks_texts = {0.0: "Undetermined State", 1.0: "Hooks Closed"}
            rs_sm_docking_flag_texts = {0.0: "Undetermined State", 1.0: "Docking Flag Active"}

            # Read indices
            ros_mode = float(values[46][0])
            rs_att_mode = float(values[126][0])
            rs_motion_control = float(values[127][0])
            rs_prep_free_drift = float(values[128][0])
            rs_thruster_operation = float(values[129][0])
            rs_current_dynamic = float(values[130][0])
            rs_kurs1_op = float(values[107][0])
            rs_kurs2_op = float(values[108][0])
            rs_p1p2_failure = float(values[109][0])
            rs_kursp_test = float(values[112][0])
            rs_functional_mode = float(values[115][0])
            rs_standby_mode = float(values[116][0])
            rs_sm_capture_signal = float(values[113][0])
            rs_target_acquisition = float(values[114][0])
            rs_sm_fwd_dock = float(values[118][0])
            rs_sm_aft_dock = float(values[119][0])
            rs_sm_nadir_dock = float(values[120][0])
            rs_fgb_nadir_dock = float(values[121][0])
            rs_sm_udm_dock = float(values[122][0])
            rs_mrm1_dock = float(values[123][0])
            rs_mrm2_dock = float(values[124][0])
            rs_sm_docking_flag = float(values[117][0])
            rs_sm_hooks = float(values[125][0])
            ros_docking_range = float(values[110][0])
            ros_rate = float(values[111][0])

            # Top mode label
            self.ids.ros_mode.text = ros_mode_texts.get(ros_mode, "n/a")

            # State labels
            self.ids.active_attitude.text = rs_att_mode_texts.get(rs_att_mode, "n/a")
            self.ids.motion_control.text = rs_motion_control_texts.get(rs_motion_control, "n/a")
            self.ids.prep_free_drift.text = rs_prep_free_drift_texts.get(rs_prep_free_drift, "n/a")
            self.ids.thruster_operation.text = rs_thruster_operation_texts.get(rs_thruster_operation, "n/a")
            self.ids.current_dynamic.text = rs_current_dynamic_texts.get(rs_current_dynamic, "n/a")

            self.ids.kurs1_operating.text = rs_signal_texts.get(rs_kurs1_op, "n/a")
            self.ids.kurs2_operating.text = rs_signal_texts.get(rs_kurs2_op, "n/a")
            self.ids.p1p2_failure.text = rs_signal_texts.get(rs_p1p2_failure, "n/a")
            self.ids.kursp_test_mode.text = rs_signal_texts.get(rs_kursp_test, "n/a")
            self.ids.functional_mode.text = rs_signal_texts.get(rs_functional_mode, "n/a")
            self.ids.standby_mode.text = rs_signal_texts.get(rs_standby_mode, "n/a")
            self.ids.sm_capture_signal.text = rs_signal_texts.get(rs_sm_capture_signal, "n/a")
            self.ids.target_acquisition.text = rs_signal_texts.get(rs_target_acquisition, "n/a")

            self.ids.sm_fwd_dock.text = rs_docking_port_texts.get(rs_sm_fwd_dock, "n/a") + " (FGB)"
            self.ids.sm_aft_dock.text = rs_vv_docking_port_texts.get(rs_sm_aft_dock, "n/a")
            self.ids.sm_nadir_dock.text = rs_docking_port_texts.get(rs_sm_nadir_dock, "n/a") + " (MLM)"
            self.ids.fgb_nadir_dock.text = rs_docking_port_texts.get(rs_fgb_nadir_dock, "n/a") + " (MRM-1)"
            self.ids.sm_udm_dock.text = rs_vv_docking_port_texts.get(rs_sm_udm_dock, "n/a")
            self.ids.mrm1_dock.text = rs_vv_docking_port_texts.get(rs_mrm1_dock, "n/a")
            self.ids.mrm2_dock.text = rs_vv_docking_port_texts.get(rs_mrm2_dock, "n/a")

            self.ids.sm_docking_flag.text = rs_sm_docking_flag_texts.get(rs_sm_docking_flag, "n/a")
            self.ids.sm_hooks.text = rs_hooks_texts.get(rs_sm_hooks, "n/a")

            # Range & rate
            if rs_target_acquisition:
                self.ids.sm_range.text = f"{ros_docking_range:0.2f} m"
                self.ids.sm_rate.text = f"{ros_rate:0.2f} m/s"
            else:
                self.ids.sm_range.text = "n/a"
                self.ids.sm_rate.text = "n/a"

            # Moving average and bar
            self._range_samples.append(ros_docking_range)
            avg_range = sum(self._range_samples) / len(self._range_samples)

            if rs_target_acquisition and avg_range <= 80000:
                self.ids.dock_in_progress.text = "DOCKING IN PROGRESS"
                self.ids.dock_in_progress.color = (0, 0, 1, 1)
                self.update_docking_bar_width(avg_range)
                if rs_sm_docking_flag:
                    self.ids.dock_in_progress.text = "DOCKING COMPLETE!"
                    self.ids.dock_in_progress.color = (0, 1, 0, 1)
            else:
                self.ids.dock_in_progress.color = (0, 0, 0, 0)
                self.update_docking_bar_width(avg_range)
        except Exception as exc:
            log_error(f"RS_Dock _update_from_db failed: {exc}")

