from __future__ import annotations

import pathlib
import json
import requests
from kivy.uix.screenmanager import Screen
from kivy.event import EventDispatcher
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.clock import Clock

from utils.serial import serialWrite          # <-- already works elsewhere

kv_path = pathlib.Path(__file__).with_name("Settings_Screen.kv")
Builder.load_file(str(kv_path))

class Settings_Screen(Screen, EventDispatcher):
    """
    User preferences screen.
    Currently: checkbox toggles SmartRolloverBGA.
    Location settings for ISS pass detection.
    """

    mimic_directory = StringProperty(
        str(pathlib.Path(__file__).resolve().parents[3])   # /home/pi/Mimic
    )

    # Preset locations for easy selection
    PRESET_LOCATIONS = {
        "Houston, TX": (29.7604, -95.3698),
        "Kennedy Space Center": (28.5729, -80.6490),
        "Moscow, Russia": (55.7558, 37.6176),
        "Tsukuba, Japan": (36.0833, 140.0833),
        "Oberpfaffenhofen, Germany": (48.0833, 11.2833),
        "Quebec, Canada": (46.8139, -71.2080),
        "London, UK": (51.5074, -0.1278),
        "Sydney, Australia": (-33.8688, 151.2093),
        "Cape Town, South Africa": (-33.9249, 18.4241),
        "São Paulo, Brazil": (-23.5505, -46.6333),
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_location = None
        self.load_location_settings()

    def on_enter(self):
        """Called when the settings screen is entered."""
        super().on_enter()
        self.update_location_display()

    def update_location_display(self):
        """Update the current location display label."""
        try:
            if self.current_location:
                # Find the closest preset location name
                closest_name = "Custom Location"
                min_distance = float('inf')
                
                for name, coords in self.PRESET_LOCATIONS.items():
                    distance = ((coords[0] - self.current_location[0])**2 + 
                              (coords[1] - self.current_location[1])**2)**0.5
                    if distance < min_distance:
                        min_distance = distance
                        closest_name = name
                
                # Update the display
                if hasattr(self, 'ids') and 'current_location_label' in self.ids:
                    self.ids.current_location_label.text = f'Current: {closest_name}'
                    
                # Update the manual input fields
                if 'lat_input' in self.ids and 'lon_input' in self.ids:
                    self.ids.lat_input.text = f'{self.current_location[0]:.4f}'
                    self.ids.lon_input.text = f'{self.current_location[1]:.4f}'
        except Exception as e:
            print(f"Failed to update location display: {e}")

    def load_location_settings(self):
        """Load saved location settings or use IP geolocation."""
        try:
            config_path = pathlib.Path.home() / ".mimic_data" / "location_config.json"
            if config_path.exists():
                with open(config_path, 'r') as f:
                    data = json.load(f)
                    self.current_location = (data['lat'], data['lon'])
                    return
            
            # No saved location, try IP geolocation
            self.detect_location_from_ip()
        except Exception as e:
            print(f"Location loading failed: {e}")
            # Default to Houston
            self.current_location = (29.7604, -95.3698)

    def detect_location_from_ip(self):
        """Detect user location from IP address."""
        try:
            # Use a free IP geolocation service
            response = requests.get('http://ip-api.com/json/', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'success':
                    self.current_location = (data['lat'], data['lon'])
                    self.save_location_settings()
                    self.update_location_display()
                    self.update_orbit_screen_location()
                    return True
        except Exception as e:
            print(f"IP geolocation failed: {e}")
        
        # Fallback to Houston
        self.current_location = (29.7604, -95.3698)
        self.update_location_display()
        return False

    def save_location_settings(self):
        """Save current location to config file."""
        try:
            if self.current_location:
                config_path = pathlib.Path.home() / ".mimic_data" / "location_config.json"
                config_path.parent.mkdir(exist_ok=True)
                
                data = {
                    'lat': self.current_location[0],
                    'lon': self.current_location[1]
                }
                
                with open(config_path, 'w') as f:
                    json.dump(data, f)
        except Exception as e:
            print(f"Location saving failed: {e}")

    def set_location_from_preset(self, location_name):
        """Set location from preset list."""
        if location_name in self.PRESET_LOCATIONS:
            self.current_location = self.PRESET_LOCATIONS[location_name]
            self.save_location_settings()
            self.update_orbit_screen_location()
            self.update_location_display()
            return True
        return False

    def set_location_from_coordinates(self, lat, lon):
        """Set location from manual coordinates."""
        try:
            lat = float(lat)
            lon = float(lon)
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                self.current_location = (lat, lon)
                self.save_location_settings()
                self.update_orbit_screen_location()
                self.update_location_display()
                return True
        except ValueError:
            pass
        return False

    def update_orbit_screen_location(self):
        """Update the orbit screen with new location."""
        try:
            # Find the orbit screen and update its location
            orbit_screen = self.manager.get_screen('orbit')
            if hasattr(orbit_screen, 'set_user_location'):
                orbit_screen.set_user_location(self.current_location[0], self.current_location[1])
        except Exception as e:
            print(f"Failed to update orbit screen: {e}")

    # ------------------------------------------------------------------
    # bound in KV:  on_active: root.checkbox_clicked(self, value)
    # ------------------------------------------------------------------
    def checkbox_clicked(self, checkbox, active: bool) -> None:
        cmd = "SmartRolloverBGA=1 " if active else "SmartRolloverBGA=0 "
        serialWrite(cmd)

