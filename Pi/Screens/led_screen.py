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
        
    def on_leave(self):
        """Called when the screen is left."""
        super().on_leave()
        log_info("LED Screen: on_leave")
        # Stop status updates
        if hasattr(self, '_status_event') and self._status_event:
            self._status_event.cancel()
            self._status_event = None
    
    # ===== SOLAR ARRAY TESTING =====
    def test_solar_array(self, array_name: str):
        """Test LED functionality for a specific solar array with current color."""
        try:
            command = f"LED_{array_name.upper()}={self._current_color}"
            log_info(f"LED Screen: Testing solar array {array_name} with {self._current_color}: {command}")
            serialWrite(command)
            self._current_test = f"Solar Array {array_name.upper()} ({self._current_color})"
            self._start_test_timer()
        except Exception as e:
            log_error(f"LED Screen: Error testing solar array {array_name}: {e}")
    
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
            command = f"PATTERN_{pattern_name.upper()}"
            log_info(f"LED Screen: Testing pattern {pattern_name}: {command}")
            serialWrite(command)
            self._current_test = f"Pattern: {pattern_name.title()}"
            self._start_test_timer()
        except Exception as e:
            log_error(f"LED Screen: Error testing pattern {pattern_name}: {e}")
    
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
            serialWrite(command)
            self._current_test = f"Animation: {animation_name.title()}"
            self._start_test_timer()
        except Exception as e:
            log_error(f"LED Screen: Error testing animation {animation_name}: {e}")
    
    def test_pulse_animation(self):
        """Test pulse animation."""
        self.test_animation("PULSE")
    
    def test_chase_animation(self):
        """Test chase animation."""
        self.test_animation("CHASE")
    
    def test_disco_animation(self):
        """Test disco animation."""
        self.test_animation("DISCO")
    
    def stop_animations(self):
        """Stop all running animations."""
        try:
            command = "ANIMATE_STOP"
            log_info(f"LED Screen: Stopping animations: {command}")
            serialWrite(command)
            self._current_test = "Animations Stopped"
            self._start_test_timer()
        except Exception as e:
            log_error(f"LED Screen: Error stopping animations: {e}")
    
    # ===== SPECIAL FUNCTIONS =====
    def turn_off_all_leds(self):
        """Turn off all LEDs."""
        try:
            command = "LED_ALL=Off"
            log_info(f"LED Screen: Turning off all LEDs: {command}")
            serialWrite(command)
            self._current_test = "All LEDs Off"
            self._start_test_timer()
        except Exception as e:
            log_error(f"LED Screen: Error turning off all LEDs: {e}")
    
    def reset_leds(self):
        """Reset all LEDs to default state."""
        try:
            command = "RESET"
            log_info(f"LED Screen: Resetting LEDs: {command}")
            serialWrite(command)
            self._current_test = "LED Reset"
            self._start_test_timer()
        except Exception as e:
            log_error(f"LED Screen: Error resetting LEDs: {e}")
    
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
            if hasattr(self, 'ids') and 'test_status' in self.ids:
                self.ids.test_status.text = self.get_test_status()
                # Change color based on status
                if hasattr(self, '_current_test') and self._current_test:
                    self.ids.test_status.color = (1, 1, 0, 1)  # Yellow when testing
                else:
                    self.ids.test_status.color = (0, 1, 0, 1)  # Green when ready
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
    
    def show_help(self):
        """Show help information about available commands."""
        try:
            help_text = "=== LED Screen Help ===\n\n"
            
            help_text += "Available Colors:\n"
            for color in self.get_available_colors():
                help_text += f"  {color}\n"
            
            help_text += "\nSolar Arrays:\n"
            help_text += "  1A, 1B, 2A, 2B, 3A, 3B, 4A, 4B\n"
            
            help_text += "\nPatterns:\n"
            for pattern in self.get_available_patterns():
                help_text += f"  {pattern}\n"
            
            help_text += "\nAnimations:\n"
            for animation in self.get_available_animations():
                help_text += f"  {animation}\n"
            
            help_text += "\nCommands Sent:\n"
            help_text += "  LED_1A=Red, PATTERN_RAINBOW, ANIMATE_PULSE, etc.\n"
            
            # Log the help text
            log_info(f"LED Screen Help:\n{help_text}")
            
            # Update status to show help
            self._current_test = "Help Displayed (see logs)"
            self._start_test_timer()
            
        except Exception as e:
            log_error(f"LED Screen: Error showing help: {e}")
