#!/usr/bin/python

import os
os.environ["KIVY_NO_CONSOLELOG"] = "0"
os.environ["KIVY_LOG_LEVEL"] = "debug"

from kivy.app import App
from kivy.lang import Builder
from pathlib import Path

# Load the KV file directly
kv_file = Path(__file__).parent / "Screens" / "Orbit_Screen.kv"
print(f"Loading KV file: {kv_file}")
print(f"File exists: {kv_file.exists()}")

try:
    # Load the KV file
    Builder.load_file(str(kv_file))
    print("✓ KV file loaded successfully")
except Exception as e:
    print(f"✗ KV file loading failed: {e}")
    import traceback
    traceback.print_exc()

class TestApp(App):
    def build(self):
        from kivy.uix.widget import Widget
        return Widget()

if __name__ == '__main__':
    TestApp().run() 