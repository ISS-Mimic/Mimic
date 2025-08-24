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
from utils.logger import log_info, log_error

kv_path = pathlib.Path(__file__).with_name("Settings_Screen.kv")
Builder.load_file(str(kv_path))

class Settings_Screen(Screen, EventDispatcher):
    """
    User preferences screen.
    Features:
    - Location settings for ISS pass detection (IP geolocation + manual input)
    - Smartflip motor control toggle
    - Automatic integration with orbit screen
    """

    mimic_directory = StringProperty(
        str(pathlib.Path(__file__).resolve().parents[3])   # /home/pi/Mimic
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_location = None
        self.load_location_settings()

    def on_enter(self):
        """Called when the settings screen is entered."""
        super().on_enter()
        self.update_location_display()
        self._start_arduino_monitoring()
        # Initialize Arduino widget
        self._initialize_arduino_widget()
        # Show current location in status bar
        self._update_status_with_current_location()
    
    def on_leave(self):
        """Called when the settings screen is left."""
        super().on_leave()
        self._stop_arduino_monitoring()

    def update_location_display(self):
        """Update the current location display and input fields."""
        try:
            if self.current_location:
                # Update the manual input fields
                if 'lat_input' in self.ids and 'lon_input' in self.ids:
                    self.ids.lat_input.text = f'{self.current_location[0]:.4f}'
                    self.ids.lon_input.text = f'{self.current_location[1]:.4f}'
        except Exception as e:
            log_error(f"Failed to update location display: {e}")

    def load_location_settings(self):
        """Load saved location settings or use IP geolocation."""
        try:
            config_path = pathlib.Path.home() / ".mimic_data" / "location_config.json"
            if config_path.exists():
                with open(config_path, 'r') as f:
                    data = json.load(f)
                    self.current_location = (data['lat'], data['lon'])
                    log_info(f"Loaded saved location: {self.current_location[0]:.4f}, {self.current_location[1]:.4f}")
                    return
            
            # No saved location, try IP geolocation
            log_info("No saved location found, attempting IP geolocation")
            self.detect_location_from_ip()
        except Exception as e:
            log_error(f"Location loading failed: {e}")
            # Default to Houston
            self.current_location = (29.7604, -95.3698)
            log_info("Using default Houston location")

    def detect_location_from_ip(self):
        """Detect user location from IP address."""
        try:
            log_info("Attempting IP geolocation...")
            # Use a free IP geolocation service
            response = requests.get('http://ip-api.com/json/', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'success':
                    self.current_location = (data['lat'], data['lon'])
                    self.save_location_settings()
                    self.update_location_display()
                    self.update_orbit_screen_location()
                    log_info(f"IP geolocation successful: {self.current_location[0]:.4f}, {self.current_location[1]:.4f}")
                    
                    # Update status message
                    if hasattr(self, 'ids') and 'status_label' in self.ids:
                        self.ids.status_label.text = f'IP location detected: {self.current_location[0]:.4f}, {self.current_location[1]:.4f}'
                        # Reset to default message after 3 seconds
                        Clock.schedule_once(lambda dt: self._reset_status_to_default(), 3.0)
                    
                    return True
        except Exception as e:
            log_error(f"IP geolocation failed: {e}")
        
        # Fallback to Houston
        self.current_location = (29.7604, -95.3698)
        self.update_location_display()
        log_info("Using fallback Houston location")
        
        # Update status message
        if hasattr(self, 'ids') and 'status_label' in self.ids:
            self.ids.status_label.text = 'Using fallback Houston location'
            # Reset to default message after 3 seconds
            Clock.schedule_once(lambda dt: self._reset_status_to_default(), 3.0)
        
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
                log_info(f"Location settings saved: {self.current_location[0]:.4f}, {self.current_location[1]:.4f}")
        except Exception as e:
            log_error(f"Location saving failed: {e}")

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
                log_info(f"Manual location set: {lat:.4f}, {lon:.4f}")
                
                # Update status message
                if hasattr(self, 'ids') and 'status_label' in self.ids:
                    self.ids.status_label.text = f'Location set to: {lat:.4f}, {lon:.4f}'
                    # Reset to default message after 3 seconds
                    Clock.schedule_once(lambda dt: self._reset_status_to_default(), 3.0)
                
                return True
            else:
                log_error(f"Invalid coordinates: {lat}, {lon} (must be lat: -90 to 90, lon: -180 to 180)")
                # Update status message
                if hasattr(self, 'ids') and 'status_label' in self.ids:
                    self.ids.status_label.text = f'Invalid coordinates: {lat}, {lon}'
        except ValueError:
            log_error(f"Invalid coordinate format: {lat}, {lon}")
            # Update status message
            if hasattr(self, 'ids') and 'status_label' in self.ids:
                self.ids.status_label.text = f'Invalid coordinate format: {lat}, {lon}'
        return False

    def update_orbit_screen_location(self):
        """Update the orbit screen with new location."""
        try:
            # Find the orbit screen and update its location
            orbit_screen = self.manager.get_screen('orbit')
            if hasattr(orbit_screen, 'set_user_location'):
                orbit_screen.set_user_location(self.current_location[0], self.current_location[1])
                log_info(f"Updated orbit screen location: {self.current_location[0]:.4f}, {self.current_location[1]:.4f}")
            else:
                log_error("Orbit screen does not have set_user_location method")
        except Exception as e:
            log_error(f"Failed to update orbit screen: {e}")

    # ------------------------------------------------------------------
    # bound in KV:  on_active: root.checkbox_clicked(self, value)
    # ------------------------------------------------------------------
    def checkbox_clicked(self, checkbox, active: bool) -> None:
        cmd = "SmartRolloverBGA=1 " if active else "SmartRolloverBGA=0 "
        serialWrite(cmd)
        log_info(f"SmartRolloverBGA toggled to {active}")
        
        # Update status message
        if hasattr(self, 'ids') and 'status_label' in self.ids:
            status_text = "Smartflip enabled, motors will transition through 0 crossover" if active else "Smartflip disabled, motors will unwind at 0 degree crossover"
            self.ids.status_label.text = status_text
            # Reset to default message after 3 seconds
            Clock.schedule_once(lambda dt: self._reset_status_to_default(), 3.0)
    
    def _start_arduino_monitoring(self):
        """Start monitoring Arduino connection status."""
        try:
            self._arduino_monitor_event = Clock.schedule_interval(self._update_arduino_status, 2.0)
            log_info("Settings Screen: Arduino monitoring started")
        except Exception as exc:
            log_error(f"Failed to start Arduino monitoring: {exc}")
    
    def _stop_arduino_monitoring(self):
        """Stop monitoring Arduino connection status."""
        try:
            if hasattr(self, '_arduino_monitor_event'):
                self._arduino_monitor_event.cancel()
            log_info("Settings Screen: Arduino monitoring stopped")
        except Exception as exc:
            log_error(f"Failed to stop Arduino monitoring: {exc}")
    
    def _update_arduino_status(self, dt):
        """Update Arduino status display."""
        try:
            if hasattr(self, 'ids') and 'arduino' in self.ids and 'arduino_count' in self.ids:
                # Check if any Arduinos are connected
                arduino_count_text = self.ids.arduino_count.text
                arduino_connected = arduino_count_text and arduino_count_text.strip() != ''
                
                if arduino_connected:
                    # Arduino connected - show no_transmit status
                    self.ids.arduino.source = f"{self.mimic_directory}/Mimic/Pi/imgs/signal/arduino_notransmit.png"
                else:
                    # No Arduino connected - show offline status
                    self.ids.arduino.source = f"{self.mimic_directory}/Mimic/Pi/imgs/signal/arduino_offline.png"
        except Exception as exc:
            log_error(f"Error updating Arduino status: {exc}")
    
    def _initialize_arduino_widget(self):
        """Initialize the Arduino widget based on connection status."""
        try:
            if hasattr(self, 'ids') and 'arduino' in self.ids:
                # Check if any Arduinos are connected
                arduino_count_label = getattr(self.ids, 'arduino_count', None)
                if arduino_count_label:
                    arduino_count_text = arduino_count_label.text.strip()
                    arduino_connected = arduino_count_text and arduino_count_text.isdigit() and int(arduino_count_text) > 0
                else:
                    arduino_connected = False
                
                if arduino_connected:
                    # Arduino connected - show no_transmit status
                    self.ids.arduino.source = f"{self.mimic_directory}/Mimic/Pi/imgs/signal/arduino_notransmit.png"
                    log_info("Settings Screen: Arduino widget initialized to no_transmit (connected)")
                else:
                    # No Arduino connected - show offline status
                    self.ids.arduino.source = f"{self.mimic_directory}/Mimic/Pi/imgs/signal/arduino_offline.png"
                    log_info("Settings Screen: Arduino widget initialized to no_transmit (not connected)")
        except Exception as exc:
            log_error(f"Failed to initialize Arduino widget: {exc}")
    
    def _reset_status_to_default(self):
        """Reset the status label to the default message."""
        try:
            if hasattr(self, 'ids') and 'status_label' in self.ids:
                # Show current location in status bar
                if hasattr(self, 'current_location') and self.current_location:
                    lat, lon = self.current_location
                    self.ids.status_label.text = f'Current: {lat:.4f}, {lon:.4f}'
                else:
                    self.ids.status_label.text = 'Adjust Location or Smartflip'
        except Exception as exc:
            log_error(f"Failed to reset status to default: {exc}")
    
    def _update_status_with_current_location(self):
        """Update the status bar to show current location."""
        try:
            if hasattr(self, 'ids') and 'status_label' in self.ids:
                if hasattr(self, 'current_location') and self.current_location:
                    lat, lon = self.current_location
                    self.ids.status_label.text = f'Current: {lat:.4f}, {lon:.4f}'
                else:
                    self.ids.status_label.text = 'Adjust Location or Smartflip'
        except Exception as exc:
            log_error(f"Failed to update status with current location: {exc}")

