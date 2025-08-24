from __future__ import annotations

import pathlib, threading      # threading only if you call it here later
from typing import Dict
from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty
from kivy.lang import Builder

from utils.serial import serialWrite
from utils.logger import log_info, log_error

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
    _default_color = (.5, .5, .5, 1)   # grey when inactive
    _active_color  = (.1, .8, .1, 1)   # green when active

    # currently selected joint label ('beta4b', 'psarj', …)
    active_joint: str | None = None
    
    # Local storage for joint angles
    _mc_angles: dict[str, float] = {
        "beta1a": 0.0, "beta1b": 0.0, "beta2a": 0.0, "beta2b": 0.0,
        "beta3a": 0.0, "beta3b": 0.0, "beta4a": 0.0, "beta4b": 0.0,
        "psarj": 0.0, "ssarj": 0.0, "ptrrj": 0.0, "strrj": 0.0
    }



    # -------------------------------------------------------------------------
    # Kivy life-cycle
    # -------------------------------------------------------------------------
    def on_pre_enter(self, *_):
        self.refresh_buttons()         # text & colour on every visit
        self._update_status("Click a joint to control it")
        self._update_button_states()
        self._initialize_arduino_widget()
        # Schedule periodic button state updates
        from kivy.clock import Clock
        self._button_update_event = Clock.schedule_interval(self._update_button_states, 2.0)  # Check every 2 seconds
    
    def on_pre_leave(self, *_):
        """Clean up scheduled updates when leaving the screen."""
        if hasattr(self, '_button_update_event'):
            self._button_update_event.cancel()

    # -------------------------------------------------------------------------
    # Public callbacks (bound in KV)
    # -------------------------------------------------------------------------
    def set_active(self, joint_key: str) -> None:
        """Called when a tile is clicked."""
        self.active_joint = joint_key
        log_info(f"ManualControl: active → {joint_key}")
        self._highlight_tiles()
        log_info(f"ManualControl: active_joint is now: {self.active_joint}")
        self._update_status(f"Selected: {joint_key.upper()}")

    def increment_active(self, delta: float) -> None:
        if self.active_joint is None:
            self._update_status("No joint selected - click a joint first")
            return
        log_info(f"ManualControl: Incrementing {self.active_joint} by {delta}")
        self._set_angle(self.active_joint, delta=delta)
        self.refresh_buttons()
        self._update_status(f"Adjusted {self.active_joint.upper()} by {delta}°")

    def set_zero(self) -> None:
        for key in self._mc_angles:
            self._set_angle(key, absolute=0)
        self.refresh_buttons()
        self._update_status("All joints set to 0°")

    def set_ninety(self) -> None:
        for key in self._mc_angles:
            self._set_angle(key, absolute=90)
        self.refresh_buttons()
        self._update_status("All joints set to 90°")

    def calibrate_zero(self) -> None:
        """Tell controller current position = 0 for every joint."""
        for key in self._mc_angles:
            try:
                serialWrite("NULLIFY=1 ")
            except Exception as exc:
                log_error(f"Serial write failed ({key}): {exc}")
            self._set_angle(key, absolute=0, emit=False)
        self.refresh_buttons()
        log_info("ManualControl: calibration sent for all joints.")
        self._update_status("Calibration sent - all joints set to 0°")

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
        new_val = absolute if absolute is not None else self._mc_angles[label] + delta
        self._mc_angles[label] = new_val
        log_info(f"ManualControl: Setting {label} to {new_val}")

        if emit:
            try:
                # Show transmit animation
                self._show_transmit_animation(True)
                
                # Map internal labels to Arduino command format
                label_mapping = {
                    'beta1a': 'B1A',
                    'beta1b': 'B1B', 
                    'beta2a': 'B2A',
                    'beta2b': 'B2B',
                    'beta3a': 'B3A',
                    'beta3b': 'B3B',
                    'beta4a': 'B4A',
                    'beta4b': 'B4B',
                    'psarj': 'PSARJ',
                    'ssarj': 'SSARJ',
                    'ptrrj': 'PTRRJ',
                    'strrj': 'STRRJ'
                }
                
                arduino_label = label_mapping.get(label, label.upper())
                cmd = f"{arduino_label}={new_val} "
                log_info(f"ManualControl: Sending command: {cmd!r}")
                serialWrite(cmd)
                
                # Hide transmit animation after a short delay
                from kivy.clock import Clock
                Clock.schedule_once(lambda dt: self._show_transmit_animation(False), 0.5)
                
            except Exception as exc:
                log_error(f"Serial write failed ({label}): {exc}")
                # Hide transmit animation on error
                self._show_transmit_animation(False)

        # Note: Database update removed - not essential for manual control functionality
        # The mc_angles are stored in memory and serial commands are sent successfully

    # -------------------------------------------------------------------------
    # Visual helpers
    # -------------------------------------------------------------------------
    def refresh_buttons(self) -> None:
        """Update angle text on every tile, then recolour."""
        a: Dict[str, float] = self._mc_angles
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
    
    def _update_status(self, message: str) -> None:
        """Update the status label with the given message."""
        try:
            if hasattr(self, 'ids') and 'status_label' in self.ids:
                self.ids.status_label.text = message
                log_info(f"ManualControl: Status updated: {message}")
        except Exception as exc:
            log_error(f"Failed to update status label: {exc}")
    
    def _update_button_states(self, dt=None) -> None:
        """Enable/disable buttons based on Arduino connection."""
        try:
            # Get arduino count from the screen's own arduino_count label
            # This gets updated by the main app's updateArduinoCount method
            arduino_count_label = getattr(self.ids, 'arduino_count', None)
            if arduino_count_label:
                arduino_count_text = arduino_count_label.text.strip()
                if arduino_count_text and arduino_count_text.isdigit():
                    arduino_count = int(arduino_count_text)
                    arduino_connected = arduino_count > 0
                else:
                    arduino_connected = False
            else:
                arduino_connected = False
            
            # Get all increment and control buttons
            control_buttons = [
                'set0', 'set90', 'calibrate_zero',
                'minus5', 'plus5', 'minus20', 'plus20', 'minus90', 'plus90'
            ]
            
            # Get all joint selection buttons
            joint_buttons = [
                'Beta1B_Button', 'Beta3B_Button', 'SSARJ_Button', 'Beta3A_Button',
                'Beta1A_Button', 'STRRJ_Button', 'PTRRJ_Button', 'PSARJ_Button',
                'Beta2A_Button', 'Beta4A_Button', 'Beta2B_Button', 'Beta4B_Button'
            ]
            
            # Disable/enable all buttons based on Arduino connection
            all_buttons = control_buttons + joint_buttons
            
            for button_id in all_buttons:
                if button_id in self.ids:
                    self.ids[button_id].disabled = not arduino_connected
            
            if not arduino_connected:
                self._update_status("No Arduinos connected - all buttons disabled")
            else:
                self._update_status("Arduinos connected - ready for manual control")
                
        except Exception as exc:
            log_error(f"Failed to update button states: {exc}")
    
    def _show_transmit_animation(self, show: bool) -> None:
        """Show or hide the transmit animation on the Arduino widget."""
        try:
            if hasattr(self, 'ids') and 'arduino' in self.ids:
                if show:
                    # Show transmit animation
                    self.ids.arduino.source = f"{self.mimic_directory}/Mimic/Pi/imgs/signal/arduino_transmit.zip"
                else:
                    # Show normal (notransmit) state
                    self.ids.arduino.source = f"{self.mimic_directory}/Mimic/Pi/imgs/signal/arduino_notransmit.png"
        except Exception as exc:
            log_error(f"Failed to update Arduino animation: {exc}")
    
    def _initialize_arduino_widget(self) -> None:
        """Initialize the Arduino widget to show notransmit state."""
        try:
            if hasattr(self, 'ids') and 'arduino' in self.ids:
                # Start with notransmit state (not offline)
                self.ids.arduino.source = f"{self.mimic_directory}/Mimic/Pi/imgs/signal/arduino_notransmit.png"
        except Exception as exc:
            log_error(f"Failed to initialize Arduino widget: {exc}")
