from __future__ import annotations

import pathlib, logging, threading      # threading only if you call it here later
from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty
from kivy.lang import Builder
from kivy.app import App

# ------------------------------------------------------------------ logging ---
log_info  = logging.getLogger("MyLogger").info
log_error = logging.getLogger("MyLogger").error

# ------------------------------------------------------------ load kv for THIS screen
kv_path = pathlib.Path(__file__).with_name("ManualControlScreen.kv")
Builder.load_file(str(kv_path))

class ManualControlScreen(Screen):
    """
    Let the user pick an ISS joint, jog it, or calibrate its zero.
    """

    # make available to KV at parse-time
    mimic_directory = StringProperty(
        str(pathlib.Path(__file__).resolve().parents[3])
    )

    # colour constants
    _default_color = (.3, .3, .3, 1)   # grey when inactive
    _active_color  = (.1, .8, .1, 1)   # green when active

    # currently selected joint label ('beta4b', 'psarj', …)
    active_joint: str | None = None

    # -------------------------------------------------------------------------
    # shorthands
    # -------------------------------------------------------------------------
    @staticmethod
    def _app():
        return App.get_running_app()

    # -------------------------------------------------------------------------
    # Kivy life-cycle
    # -------------------------------------------------------------------------
    def on_pre_enter(self, *_):
        self.refresh_buttons()         # text & colour on every visit

    # -------------------------------------------------------------------------
    # Public callbacks (bound in KV)
    # -------------------------------------------------------------------------
    def set_active(self, joint_key: str) -> None:
        """Called when a tile is clicked."""
        self.active_joint = joint_key
        log_info(f"ManualControl: active → {joint_key}")
        self._highlight_tiles()

    def increment_active(self, delta: float) -> None:
        if self.active_joint is None:
            return
        self._set_angle(self.active_joint, delta=delta)
        self.refresh_buttons()

    def set_zero(self) -> None:
        for key in self._app().mc_angles:
            self._set_angle(key, absolute=0)
        self.refresh_buttons()

    def set_ninety(self) -> None:
        for key in self._app().mc_angles:
            self._set_angle(key, absolute=90)
        self.refresh_buttons()

    def calibrate_zero(self) -> None:
        """Tell controller current position = 0 for every joint."""
        app = self._app()
        for key in app.mc_angles:
            try:
                serialWrite("NULLIFY=1 ")
            except Exception as exc:
                log_error(f"Serial write failed ({key}): {exc}")
            self._set_angle(key, absolute=0, emit=False)
        self.refresh_buttons()
        log_info("ManualControl: calibration sent for all joints.")

    # -------------------------------------------------------------------------
    # Core angle setter  (emit=False skips move cmd; used by calibration)
    # -------------------------------------------------------------------------
    def _set_angle(
        self,
        label: str,
        *,
        delta: float | None = None,
        absolute: float | None = None,
        emit: bool = True
    ) -> None:
        app = self._app()
        new_val = absolute if absolute is not None else app.mc_angles[label] + delta
        app.mc_angles[label] = new_val

        if emit:
            try:
                serialWrite(f"{label.upper()}={new_val} ")
            except Exception as exc:
                log_error(f"Serial write failed ({label}): {exc}")

        try:
            app.db_cursor.execute(
                "UPDATE telemetry SET Value = ? WHERE Label = ?",
                (new_val, label)
            )
        except Exception as exc:
            log_error(f"DB update failed ({label}): {exc}")

    # -------------------------------------------------------------------------
    # Visual helpers
    # -------------------------------------------------------------------------
    def refresh_buttons(self) -> None:
        """Update angle text on every tile, then recolour."""
        a: Dict[str, float] = self._app().mc_angles
        ids = self.ids

        ids.Beta4B_Button.text = f"4B\n{int(a['beta4b'])}"
        ids.Beta4A_Button.text = f"4A\n{int(a['beta4a'])}"
        ids.Beta3B_Button.text = f"3B\n{int(a['beta3b'])}"
        ids.Beta3A_Button.text = f"3A\n{int(a['beta3a'])}"
        ids.Beta2B_Button.text = f"2B\n{int(a['beta2b'])}"
        ids.Beta2A_Button.text = f"2A\n{int(a['beta2a'])}"
        ids.Beta1B_Button.text = f"1B\n{int(a['beta1b'])}"
        ids.Beta1A_Button.text = f"1A\n{int(a['beta1a'])}"
        ids.PSARJ_Button.text  = f"PSARJ {int(a['psarj'])}"
        ids.SSARJ_Button.text  = f"SSARJ {int(a['ssarj'])}"
        ids.PTRRJ_Button.text  = f"PTRRJ\n{int(a['ptrrj'])}"
        ids.STRRJ_Button.text  = f"STRRJ\n{int(a['strrj'])}"

        self._highlight_tiles()

    def _highlight_tiles(self) -> None:
        """Colour the active tile green, others grey."""
        mapping = {
            "beta4b":  "Beta4B_Button",
            "beta4a":  "Beta4A_Button",
            "beta3b":  "Beta3B_Button",
            "beta3a":  "Beta3A_Button",
            "beta2b":  "Beta2B_Button",
            "beta2a":  "Beta2A_Button",
            "beta1b":  "Beta1B_Button",
            "beta1a":  "Beta1A_Button",
            "psarj":   "PSARJ_Button",
            "ssarj":   "SSARJ_Button",
            "ptrrj":   "PTRRJ_Button",
            "strrj":   "STRRJ_Button",
        }
        for joint, wid in mapping.items():
            self.ids[wid].background_color = (
                self._active_color if joint == self.active_joint
                else self._default_color
            )
