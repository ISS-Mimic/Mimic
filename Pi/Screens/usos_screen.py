from __future__ import annotations
from kivy.uix.screenmanager import Screen
import pathlib
from kivy.lang import Builder
from ._base import MimicBase

kv_path = pathlib.Path(__file__).with_name("USOS_Screen.kv")
Builder.load_file(str(kv_path))

class USOS_Screen(MimicBase):
    pass
