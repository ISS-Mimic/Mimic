from __future__ import annotations
from kivy.uix.screenmanager import Screen
import pathlib
from kivy.lang import Builder
from kivy.clock import Clock
from ._base import MimicBase
from utils.logger import log_info, log_error

kv_path = pathlib.Path(__file__).with_name("VV_Image.kv")
Builder.load_file(str(kv_path))

class VV_Image(MimicBase):
    """
    Visiting Vehicle (VV) Image screen.
    Periodically reloads the image at {mimic_data_directory}/vv.png to reflect updates.
    """

    _update_event = None

    def on_enter(self):
        """Start periodic refresh when screen is shown."""
        try:
            # Immediate update and then periodic refresh
            self.update_vv_image(0)
            self._update_event = Clock.schedule_interval(self.update_vv_image, 67)
            log_info("VV_Image: started periodic image refresh (67s)")
        except Exception as exc:
            log_error(f"VV_Image on_enter failed: {exc}")

    def on_leave(self):
        """Stop periodic refresh when leaving the screen."""
        try:
            if self._update_event is not None:
                Clock.unschedule(self._update_event)
                self._update_event = None
                log_info("VV_Image: stopped periodic image refresh")
        except Exception as exc:
            log_error(f"VV_Image on_leave failed: {exc}")

    def update_vv_image(self, _dt):
        """Reload the VV image from the data directory."""
        try:
            if 'VVimage' in self.ids:
                self.ids.VVimage.source = f"{self.mimic_data_directory}/vv.png"
                self.ids.VVimage.reload()
        except Exception as exc:
            log_error(f"VV_Image update failed: {exc}")
