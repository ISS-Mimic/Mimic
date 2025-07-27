from __future__ import annotations
from kivy.uix.screenmanager import Screen
import pathlib
from kivy.properties import StringProperty
from kivy.lang import Builder
from ._base import MimicBase

kv_path = pathlib.Path(__file__).with_name("ISS_Screen.kv")
Builder.load_file(str(kv_path))

class ISS_Screen(MimicBase):
    """
    Shows station layout; user taps a module ? highlight it.
    `selected_module` is kept both on the Screen instance *and*
    mirrored up to `App.get_running_app().current_module`
    so other screens can read it - cleaner than a global variable
    """

    selected_module = StringProperty("")

    # ------------------------------------------------------------------
    # bound in KV:  on_press: root.select_module("US LAB")
    # ------------------------------------------------------------------")

    def select_module(self, mod_name: str) -> None:
        self.selected_module = mod_name

        App.get_running_app().current_module = mod_name

        log_info(f"ISS Screen: selected -> {mod_name}")

