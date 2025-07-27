from __future__ import annotations

import pathlib
from kivy.uix.screenmanager import Screen
from kivy.event import EventDispatcher
from kivy.lang import Builder
from kivy.properties import StringProperty

from utils.serial import serialWrite          # <-- already works elsewhere

kv_path = pathlib.Path(__file__).with_name("Settings_Screen.kv")
Builder.load_file(str(kv_path))

class Settings_Screen(Screen, EventDispatcher):
    """
    User preferences screen.
    Currently: checkbox toggles SmartRolloverBGA.
    """

    mimic_directory = StringProperty(
        str(pathlib.Path(__file__).resolve().parents[3])   # /home/pi/Mimic
    )

    # ------------------------------------------------------------------
    # bound in KV:  on_active: root.checkbox_clicked(self, value)
    # ------------------------------------------------------------------
    def checkbox_clicked(self, checkbox, active: bool) -> None:
        cmd = "SmartRolloverBGA=1 " if active else "SmartRolloverBGA=0 "
        serialWrite(cmd)

