from __future__ import annotations
from kivy.uix.screenmanager import Screen
import pathlib
from kivy.lang import Builder
from kivy.clock import Clock
from utils.logger import log_info, log_error
from utils.serial import serialWrite
from ._base import MimicBase

kv_path = pathlib.Path(__file__).with_name("LED_Screen.kv")
Builder.load_file(str(kv_path))

class LED_Screen(MimicBase):
    """
    LED testing interface for the ISS mimic model.
    Provides buttons to test LEDs on solar arrays, ISS modules, and special functions.
    Now uses the new Arduino command format with named colors and patterns.
    """
    
    mimic_directory = pathlib.Path(__file__).resolve().parents[3]   # …/Mimic
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize attributes immediately to avoid KV file errors
        self._test_mode = False
        self._current_test = None
        self._current_color = "White"
        self._status_event = None
        log_info("LED Screen: __init__ complete")
        
    def on_enter(self):
        """Called when the screen is entered."""
        super().on_enter()
        log_info("LED Screen: on_enter")
        # Start status updates
        self._status_event = Clock.schedule_interval(self._update_status, 0.5)
        # Start Arduino monitoring
        self._start_arduino_monitoring()
        # Initialize Arduino widget to correct state
        self._initialize_arduino_widget()
        
    def on_leave(self):
        """Called when the screen is left."""
        super().on_leave()
        log_info("LED Screen: on_leave")
        # Stop status updates
        if hasattr(self, '_status_event') and self._status_event:
            self._status_event.cancel()
            self._status_event = None
        # Stop Arduino monitoring
        self._stop_arduino_monitoring()
    
    # ===== SOLAR ARRAY TESTING =====
    def test_solar_array(self, array_name: str):
        """Test LED functionality for a specific solar array with current color."""
        try:
            # Check if button is enabled (Arduino connected)
            button_id = f'test_{array_name.lower()}'
            if hasattr(self, 'ids') and button_id in self.ids:
                if self.ids[button_id].disabled:
                    log_info(f"LED Screen: Button {button_id} is disabled - no Arduino connected")
                    return
            
            command = f"LED_{array_name.upper()}={self._current_color}"
            log_info(f"LED Screen: Testing solar array {array_name} with {self._current_color}: {command}")
            
            # Show transmit animation
            self._show_transmit_animation(True)
            
            serialWrite(command)
            self._current_test = f"Solar Array {array_name.upper()} ({self._current_color})"
            self._start_test_timer()
            
            # Hide transmit animation after a short delay
            Clock.schedule_once(lambda dt: self._show_transmit_animation(False), 0.5)
        except Exception as e:
            log_error(f"LED Screen: Error testing solar array {array_name}: {e}")
            # Hide transmit animation on error
            self._show_transmit_animation(False)
    
    def set_color(self, color_name: str):
        """Set the current color for LED testing."""
        try:
            self._current_color = color_name
            log_info(f"LED Screen: Color set to {color_name}")
            # Update status to show color change
            self._current_test = f"Color: {color_name}"
            self._start_test_timer()
        except Exception as e:
            log_error(f"LED Screen: Error setting color {color_name}: {e}")
    
    # ===== PATTERN TESTING =====
    def test_pattern(self, pattern_name: str):
        """Test a specific LED pattern."""
        try:
            # Check if button is enabled (Arduino connected)
            if hasattr(self, 'ids') and 'test_pattern' in self.ids:
                if self.ids.test_pattern.disabled:
                    log_info("LED Screen: Pattern button is disabled - no Arduino connected")
                    return
            
            command = f"PATTERN_{pattern_name.upper()}"
            log_info(f"LED Screen: Testing pattern {pattern_name}: {command}")
            
            # Show transmit animation
            self._show_transmit_animation(True)
            
            serialWrite(command)
            self._current_test = f"Pattern: {pattern_name.title()}"
            self._start_test_timer()
            
            # Hide transmit animation after a short delay
            Clock.schedule_once(lambda dt: self._show_transmit_animation(False), 0.5)
        except Exception as e:
            log_error(f"LED Screen: Error testing pattern {pattern_name}: {e}")
            # Hide transmit animation on error
            self._show_transmit_animation(False)
    
    def test_rainbow_pattern(self):
        """Test rainbow pattern."""
        self.test_pattern("RAINBOW")
    
    def test_alternating_pattern(self):
        """Test alternating pattern."""
        self.test_pattern("ALTERNATING")
    
    def test_red_alert_pattern(self):
        """Test red alert pattern."""
        self.test_pattern("RED_ALERT")
    
    def test_blue_pattern(self):
        """Test blue pattern."""
        self.test_pattern("BLUE_PATTERN")
    
    # ===== ANIMATION TESTING =====
    def test_animation(self, animation_name: str):
        """Test a specific LED animation."""
        try:
            command = f"ANIMATE_{animation_name.upper()}"
            log_info(f"LED Screen: Testing animation {animation_name}: {command}")
            
            # Show transmit animation
            self._show_transmit_animation(True)
            
            serialWrite(command)
            self._current_test = f"Animation: {animation_name.title()}"
            self._start_test_timer()
            
            # Hide transmit animation after a short delay
            Clock.schedule_once(lambda dt: self._show_transmit_animation(False), 0.5)
        except Exception as e:
            log_error(f"LED Screen: Error testing animation {animation_name}: {e}")
            # Hide transmit animation on error
            self._show_transmit_animation(False)
    
    def test_pulse_animation(self):
        """Test pulse animation."""
        self.test_animation("PULSE")
    
    def test_chase_animation(self):
        """Test chase animation."""
        self.test_animation("CHASE")
    
    def test_disco_animation(self):
        """Test disco animation."""
        self.test_animation("DISCO")
    
    def test_disco_mode(self):
        """Test disco mode (alias for disco animation)."""
        self.test_animation("DISCO")
    
    def stop_animations(self):
        """Stop all running animations."""
        try:
            command = "ANIMATE_STOP"
            log_info(f"LED Screen: Stopping animations: {command}")
            
            # Show transmit animation
            self._show_transmit_animation(True)
            
            serialWrite(command)
            self._current_test = "Animations Stopped"
            self._start_test_timer()
            
            # Hide transmit animation after a short delay
            Clock.schedule_once(lambda dt: self._show_transmit_animation(False), 0.5)
        except Exception as e:
            log_error(f"LED Screen: Error stopping animations: {e}")
            # Hide transmit animation on error
            self._show_transmit_animation(False)
    
    # ===== SPECIAL FUNCTIONS =====
    def light_everything(self):
        """Turn on all LEDs to current color."""
        try:
            command = f"LED_ALL={self._current_color}"
            log_info(f"LED Screen: Lighting everything {self._current_color}: {command}")
            
            # Show transmit animation
            self._show_transmit_animation(True)
            
            serialWrite(command)
            self._current_test = f"All LEDs: {self._current_color}"
            self._start_test_timer()
            
            # Hide transmit animation after a short delay
            Clock.schedule_once(lambda dt: self._show_transmit_animation(False), 0.5)
        except Exception as e:
            log_error(f"LED Screen: Error lighting everything: {e}")
            # Hide transmit animation on error
            self._show_transmit_animation(False)
    
    def turn_off_all_leds(self):
        """Turn off all LEDs."""
        try:
            command = "LED_ALL=Off"
            log_info(f"LED Screen: Turning off all LEDs: {command}")
            
            # Show transmit animation
            self._show_transmit_animation(True)
            
            serialWrite(command)
            self._current_test = "All LEDs Off"
            self._start_test_timer()
            
            # Hide transmit animation after a short delay
            Clock.schedule_once(lambda dt: self._show_transmit_animation(False), 0.5)
        except Exception as e:
            log_error(f"LED Screen: Error turning off all LEDs: {e}")
            # Hide transmit animation on error
            self._show_transmit_animation(False)
    
    def turn_off_all(self):
        """Turn off all LEDs (alias for turn_off_all_leds)."""
        self.turn_off_all_leds()
    
    def reset_leds(self):
        """Reset all LEDs to default state."""
        try:
            command = "RESET"
            log_info(f"LED Screen: Resetting LEDs: {command}")
            
            # Show transmit animation
            self._show_transmit_animation(True)
            
            serialWrite(command)
            self._current_test = "LED Reset"
            self._start_test_timer()
            
            # Hide transmit animation after a short delay
            Clock.schedule_once(lambda dt: self._show_transmit_animation(False), 0.5)
        except Exception as e:
            log_error(f"LED Screen: Error resetting LEDs: {e}")
            # Hide transmit animation on error
            self._show_transmit_animation(False)
    
    # ===== UTILITY FUNCTIONS =====
    def _start_test_timer(self):
        """Start a timer to automatically turn off test mode after 5 seconds."""
        try:
            if self._current_test:
                Clock.schedule_once(self._end_test, 5.0)
        except Exception as e:
            log_error(f"LED Screen: Error starting test timer: {e}")
    
    def _end_test(self, dt):
        """End the current test mode."""
        try:
            if self._current_test and not any(word in self._current_test.lower() for word in ['animation', 'disco', 'pulse', 'chase']):
                log_info(f"LED Screen: Ending test: {self._current_test}")
                self._current_test = None
        except Exception as e:
            log_error(f"LED Screen: Error ending test: {e}")
    
    def get_test_status(self) -> str:
        """Get the current test status for display."""
        try:
            # Simple, safe access to attributes
            if hasattr(self, '_current_test') and self._current_test:
                return f"Testing: {self._current_test}"
            if hasattr(self, '_current_color'):
                return f"Ready - Color: {self._current_color}"
            return "Initializing..."
        except Exception as e:
            log_error(f"LED Screen: Error in get_test_status: {e}")
            return "Status: Error"
    
    def _update_status(self, dt):
        """Update the test status display."""
        try:
            if hasattr(self, 'ids') and 'status_label' in self.ids:
                self.ids.status_label.text = self.get_test_status()
                # Change color based on status
                if hasattr(self, '_current_test') and self._current_test:
                    self.ids.status_label.color = (1, 1, 0, 1)  # Yellow when testing
                else:
                    self.ids.status_label.color = (0, 1, 0, 1)  # Green when ready
        except Exception as e:
            log_error(f"LED Screen: Error updating status: {e}")
    
    def get_available_colors(self) -> list:
        """Get list of available colors for the interface."""
        return [
            "Red", "Green", "Blue", "White", "Yellow", "Magenta", "Cyan", 
            "Orange", "Purple", "Pink", "Gold", "Silver", "Off"
        ]
    
    def get_available_patterns(self) -> list:
        """Get list of available patterns."""
        return ["Rainbow", "Alternating", "Red_Alert", "Blue_Pattern"]
    
    def get_available_animations(self) -> list:
        """Get list of available animations."""
        return ["Pulse", "Chase", "Disco"]
    
    def _show_transmit_animation(self, show: bool) -> None:
        """Show or hide the transmit animation on the Arduino widget."""
        try:
            if hasattr(self, 'ids') and 'arduino' in self.ids:
                if show:
                    # Show transmit animation
                    self.ids.arduino.source = f"{self.mimic_directory}/Mimic/Pi/imgs/signal/arduino_transmit.zip"
                else:
                    # Check if Arduino is connected to determine what to show
                    arduino_count_label = getattr(self.ids, 'arduino_count', None)
                    if arduino_count_label:
                        arduino_count_text = arduino_count_label.text.strip()
                        arduino_connected = arduino_count_text and arduino_count_text.isdigit() and int(arduino_count_text) > 0
                    else:
                        arduino_connected = False
                    
                    if arduino_connected:
                        # Arduino connected - show no_transmit status
                        self.ids.arduino.source = f"{self.mimic_directory}/Mimic/Pi/imgs/signal/arduino_notransmit.png"
                    else:
                        # No Arduino connected - show offline status
                        self.ids.arduino.source = f"{self.mimic_directory}/Mimic/Pi/imgs/signal/arduino_offline.png"
        except Exception as exc:
            log_error(f"Failed to update Arduino animation: {exc}")
    
    def _initialize_arduino_widget(self) -> None:
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
                    log_info("LED Screen: Arduino widget initialized to no_transmit (connected)")
                else:
                    # No Arduino connected - show offline status
                    self.ids.arduino.source = f"{self.mimic_directory}/Mimic/Pi/imgs/signal/arduino_offline.png"
                    log_info("LED Screen: Arduino widget initialized to offline (not connected)")
        except Exception as exc:
            log_error(f"Failed to initialize Arduino widget: {exc}")
    
    def _start_arduino_monitoring(self):
        """Start monitoring Arduino connection status."""
        try:
            self._arduino_monitor_event = Clock.schedule_interval(self._update_button_states, 2.0)
            log_info("LED Screen: Arduino monitoring started")
        except Exception as exc:
            log_error(f"Failed to start Arduino monitoring: {exc}")
    
    def _stop_arduino_monitoring(self):
        """Stop monitoring Arduino connection status."""
        try:
            if hasattr(self, '_arduino_monitor_event'):
                self._arduino_monitor_event.cancel()
            log_info("LED Screen: Arduino monitoring stopped")
        except Exception as exc:
            log_error(f"Failed to stop Arduino monitoring: {exc}")
    
    def _update_button_states(self, dt=None):
        """Update button states based on Arduino connection status."""
        try:
            if hasattr(self, 'ids') and 'arduino_count' in self.ids:
                # Check if any Arduinos are connected
                arduino_count_text = self.ids.arduino_count.text
                arduino_connected = arduino_count_text and arduino_count_text.strip() != ''
                
                log_info(f"LED Screen: Arduino connected: {arduino_connected}, count: '{arduino_count_text}'")
                
                # Find all buttons in the screen by searching through children
                def find_and_update_buttons(widget):
                    """Recursively find and update button states."""
                    if hasattr(widget, 'children'):
                        for child in widget.children:
                            if hasattr(child, 'text') and hasattr(child, 'on_release'):
                                # This is a button with text and on_release (our LED control buttons)
                                if child.text in ['1A', '1B', '2A', '2B', '3A', '3B', '4A', '4B', 
                                                'Pulse', 'Chase', 'Disco', 'Stop', 'Light All', 'All Off', 'Reset']:
                                    log_info(f"LED Screen: Found button '{child.text}', setting disabled={not arduino_connected}")
                                    child.disabled = not arduino_connected
                                    # Update button appearance
                                    if arduino_connected:
                                        child.opacity = 1.0
                                        # Restore original colors based on button type
                                        if child.text in ['1A', '1B', '2A', '2B', '3A', '3B', '4A', '4B']:
                                            child.background_color = (0.2, 0.6, 1, 1)  # Blue for solar arrays
                                        elif child.text in ['Pulse', 'Light All']:
                                            child.background_color = (0.3, 1, 0.3, 1)  # Green
                                        elif child.text in ['Chase', 'Reset']:
                                            child.background_color = (1, 0.6, 0.3, 1)  # Orange
                                        elif child.text == 'Disco':
                                            child.background_color = (1, 0.3, 0.8, 1)  # Pink
                                        elif child.text == 'Stop':
                                            child.background_color = (0.8, 0.3, 0.3, 1)  # Red
                                        elif child.text == 'All Off':
                                            child.background_color = (0.8, 0.3, 0.3, 1)  # Red
                                    else:
                                        child.opacity = 0.5
                                        child.background_color = (0.5, 0.5, 0.5, 1)  # Gray when disabled
                            # Recursively search children
                            find_and_update_buttons(child)
                
                # Start searching from the root widget
                find_and_update_buttons(self)
                
                # Update status message
                if hasattr(self, 'ids') and 'status_label' in self.ids:
                    if arduino_connected:
                        # Don't override user action status messages
                        if not self._current_test:
                            self.ids.status_label.text = f'Arduinos connected: {arduino_count_text}'
                    else:
                        # Always show disconnection message
                        self.ids.status_label.text = 'No Arduinos connected - LED controls disabled'
                        
        except Exception as exc:
            log_error(f"Failed to update button states: {exc}")