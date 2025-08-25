# Pi/Screens/_base.py
from pathlib import Path
from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, ObjectProperty

class MimicBase(Screen):
    mimic_directory = StringProperty(
        str(Path(__file__).resolve().parents[3])
    )
    mimic_data_directory = Path.home() / ".mimic_data"
    signalcolor = ObjectProperty([1, 1, 1])

