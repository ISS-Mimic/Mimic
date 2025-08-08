#!/usr/bin/python

import os
os.environ["KIVY_NO_CONSOLELOG"] = "0"
os.environ["KIVY_LOG_LEVEL"] = "debug"

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager
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
        
        # Test user location functionality
        print("Testing user location functionality:")
        print(f"Default location: {orbit_screen.user_lat}, {orbit_screen.user_lon}")
        
        # Test setting a new location
        orbit_screen.set_user_location(40.7128, -74.0060)  # New York
        print(f"New location: {orbit_screen.user_lat}, {orbit_screen.user_lon}")
        
        # Test another location
        orbit_screen.set_user_location(34.0522, -118.2437)  # Los Angeles
        print(f"Another location: {orbit_screen.user_lat}, {orbit_screen.user_lon}")
        
        return sm

if __name__ == '__main__':
    TestApp().run() 