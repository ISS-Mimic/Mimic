#!/usr/bin/python

import os
os.environ["KIVY_NO_CONSOLELOG"] = "0"   # Enable console logging
os.environ["KIVY_LOG_LEVEL"] = "debug"   # Enable debug logging

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty
from pathlib import Path

# Import the orbit screen
from Screens.orbit_screen import Orbit_Screen

class TestApp(App):
    def build(self):
        # Create a simple screen manager
        sm = ScreenManager()
        
        # Add the orbit screen
        orbit_screen = Orbit_Screen(name='orbit')
        sm.add_widget(orbit_screen)
        
        # Print available widget IDs
        print("Available widget IDs in orbit screen:")
        for widget_id in orbit_screen.ids.keys():
            print(f"  - {widget_id}")
        
        # Test specific widgets
        print("\nTesting specific widgets:")
        test_widgets = ['iss_track_line_a', 'iss_track_line_b', 'TDRS6', 'TDRS7', 'ZOE', 'ZOElabel']
        for widget_id in test_widgets:
            if widget_id in orbit_screen.ids:
                print(f"  ✓ {widget_id} - FOUND")
            else:
                print(f"  ✗ {widget_id} - MISSING")
        
        return sm

if __name__ == '__main__':
    TestApp().run() 