from __future__ import annotations

import pathlib, logging
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.clock import Clock

from ._base import MimicBase                        # common mimic_directory / signalcolor

log_info = logging.getLogger("MyLogger").info

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
        width, _ = Window.size
        mapped = max(0.0, 1 - value / 80_000)
        new_w  = width * 0.325 * mapped
        self.ids.docking_bar.size = (new_w, self.ids.docking_bar.height)
        self.ids.dock_layout.do_layout()

