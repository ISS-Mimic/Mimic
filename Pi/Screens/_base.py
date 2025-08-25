# Pi/Screens/_base.py
from pathlib import Path
from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, ObjectProperty
from kivy.clock import Clock
from utils.logger import log_info, log_error

class MimicBase(Screen):
    mimic_directory = StringProperty(
        str(Path(__file__).resolve().parents[3])
    )
    mimic_data_directory = Path.home() / ".mimic_data"
    signalcolor = ObjectProperty([1, 1, 1])
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Arduino monitoring
        self._arduino_event = None
    
    def on_enter(self):
        """Called when entering the screen."""
        super().on_enter()
        # Start Arduino monitoring
        self._start_arduino_monitoring()
    
    def on_leave(self):
        """Called when leaving the screen."""
        super().on_leave()
        # Stop Arduino monitoring
        self._stop_arduino_monitoring()
    
    def _start_arduino_monitoring(self):
        """Start monitoring Arduino connection status."""
        try:
            if self._arduino_event:
                return
            
            # Start Arduino monitoring every 1 second
            self._arduino_event = Clock.schedule_interval(self._update_arduino_status, 1.0)
            log_info(f"{self.__class__.__name__}: Arduino monitoring started")
            
        except Exception as exc:
            log_error(f"Failed to start Arduino monitoring: {exc}")
    
    def _stop_arduino_monitoring(self):
        """Stop monitoring Arduino connection status."""
        try:
            if self._arduino_event:
                self._arduino_event.cancel()
                self._arduino_event = None
                log_info(f"{self.__class__.__name__}: Arduino monitoring stopped")
                
        except Exception as exc:
            log_error(f"Failed to stop Arduino monitoring: {exc}")
    
    def _update_arduino_status(self, dt):
        """Update Arduino connection status and widget."""
        try:
            # Get Arduino count using the same logic as GUI.py
            import GUI
            arduino_count = len(GUI.OPEN_SERIAL_PORTS) if hasattr(GUI, 'OPEN_SERIAL_PORTS') else 0
            
            # Update Arduino count label
            if hasattr(self, 'ids') and 'arduino_count' in self.ids:
                if arduino_count > 0:
                    self.ids.arduino_count.text = str(arduino_count)
                else:
                    self.ids.arduino_count.text = ''
            
            # Update Arduino widget image
            if hasattr(self, 'ids') and 'arduino' in self.ids:
                if arduino_count > 0:
                    # Show connected status
                    self.ids.arduino.source = f"{self.mimic_directory}/Mimic/Pi/imgs/signal/arduino_notransmit.png"
                else:
                    # Show offline status
                    self.ids.arduino.source = f"{self.mimic_directory}/Mimic/Pi/imgs/signal/arduino_offline.png"
                    
        except Exception as exc:
            log_error(f"Failed to update Arduino status: {exc}")
    
    def _show_transmit_animation(self):
        """Show Arduino transmit animation briefly."""
        try:
            if hasattr(self, 'ids') and 'arduino' in self.ids:
                # Show transmit animation
                self.ids.arduino.source = f"{self.mimic_directory}/Mimic/Pi/imgs/signal/arduino_transmit.png"
                
                # Schedule return to normal state after 200ms
                Clock.schedule_once(self._return_to_normal_arduino, 0.2)
                
        except Exception as exc:
            log_error(f"Failed to show transmit animation: {exc}")
    
    def _return_to_normal_arduino(self, dt):
        """Return Arduino widget to normal state."""
        try:
            if hasattr(self, 'ids') and 'arduino' in self.ids:
                # Get Arduino count using the same logic as GUI.py
                import GUI
                arduino_count = len(GUI.OPEN_SERIAL_PORTS) if hasattr(GUI, 'OPEN_SERIAL_PORTS') else 0
                
                if arduino_count > 0:
                    # Show connected status
                    self.ids.arduino.source = f"{self.mimic_directory}/Mimic/Pi/imgs/signal/arduino_notransmit.png"
                    self.ids.arduino_count.text = str(arduino_count)
                else:
                    # Show offline status
                    self.ids.arduino.source = f"{self.mimic_directory}/Mimic/Pi/imgs/signal/arduino_offline.png"
                    self.ids.arduino_count.text = ''
                    
        except Exception as exc:
            log_error(f"Failed to return Arduino to normal state: {exc}")

