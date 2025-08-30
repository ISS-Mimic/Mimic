from __future__ import annotations
from kivy.uix.screenmanager import Screen
import pathlib
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.properties import StringProperty, NumericProperty, ObjectProperty
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
import ephem
import math
import time
import json
from datetime import datetime, timedelta
from typing import Optional, Tuple, List
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_agg import FigureCanvasAgg
import io
import numpy as np
from ._base import MimicBase
from utils.logger import log_info, log_error

kv_path = pathlib.Path(__file__).with_name("Orbit_Pass.kv")
Builder.load_file(str(kv_path))


class SkyChartWidget(Widget):
    """Custom widget for displaying the sky chart with ISS pass arc."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pass_data = None
        self.user_location = None
        self.bind(size=self._update_sky_chart, pos=self._update_sky_chart)
    
    def set_pass_data(self, pass_data: dict, user_location: Tuple[float, float]):
        """Set the pass data and user location for the sky chart."""
        self.pass_data = pass_data
        self.user_location = user_location
        self._update_sky_chart()
    
    def _update_sky_chart(self, *args):
        """Update the sky chart display."""
        if not self.pass_data or not self.user_location:
            return
        
        self.canvas.clear()
        
        # Create matplotlib figure for the sky chart
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={'projection': 'polar'})
        
        # Set up the polar plot (azimuth vs elevation)
        ax.set_theta_direction(-1)  # Clockwise from North
        ax.set_theta_zero_location('N')
        ax.set_rlim(0, 90)  # 0° to 90° elevation
        ax.set_rticks([0, 15, 30, 45, 60, 75, 90])
        ax.set_yticklabels(['0°', '15°', '30°', '45°', '60°', '75°', '90°'])
        
        # Add cardinal directions
        ax.text(0, 95, 'N', ha='center', va='center', fontsize=12, weight='bold')
        ax.text(math.pi/2, 95, 'E', ha='center', va='center', fontsize=12, weight='bold')
        ax.text(math.pi, 95, 'S', ha='center', va='center', fontsize=12, weight='bold')
        ax.text(3*math.pi/2, 95, 'W', ha='center', va='center', fontsize=12, weight='bold')
        
        # Plot the ISS pass arc
        if 'azimuths' in self.pass_data and 'elevations' in self.pass_data:
            az = np.radians(self.pass_data['azimuths'])
            el = self.pass_data['elevations']
            
            # Convert to radians for polar plot
            az_rad = np.radians(self.pass_data['azimuths'])
            
            # Plot the pass arc
            ax.plot(az_rad, el, 'r-', linewidth=3, label='ISS Pass')
            
            # Mark key points
            if 'max_elevation_time' in self.pass_data:
                max_el_idx = np.argmax(el)
                ax.plot(az_rad[max_el_idx], el[max_el_idx], 'ro', markersize=8, label='Max Elevation')
            
            # Mark start and end points
            if len(az) > 0:
                ax.plot(az_rad[0], el[0], 'go', markersize=6, label='Pass Start')
                ax.plot(az_rad[-1], el[-1], 'mo', markersize=6, label='Pass End')
        
        # Add grid and legend
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper right')
        ax.set_title('ISS Pass Sky Chart', pad=20, fontsize=14, weight='bold')
        
        # Convert matplotlib figure to image
        canvas = FigureCanvasAgg(fig)
        canvas.draw()
        
        # Get the image data
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        buf.seek(0)
        
        # Create Kivy image from the buffer
        from kivy.core.image import Image as CoreImage
        from kivy.graphics.texture import Texture
        
        # Load the image data
        image_data = buf.getvalue()
        buf.close()
        
        # Create texture
        texture = Texture.create(size=(800, 800), colorfmt='rgba')
        texture.blit_buffer(image_data, colorfmt='rgba', bufferfmt='ubyte')
        
        # Draw the texture
        with self.canvas:
            Color(1, 1, 1, 1)
            Rectangle(texture=texture, pos=self.pos, size=self.size)
        
        plt.close(fig)


class Orbit_Pass(MimicBase):
    """Screen for displaying ISS pass predictions and sky charts."""
    
    # Properties for pass information
    pass_start_time = StringProperty("")
    pass_end_time = StringProperty("")
    pass_duration = StringProperty("")
    max_elevation = StringProperty("")
    start_azimuth = StringProperty("")
    end_azimuth = StringProperty("")
    magnitude = StringProperty("")
    pass_quality = StringProperty("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user_location = None
        self.iss_tle = None
        self.next_pass_data = None
        self.sky_chart_widget = None
        self._pass_update_event = None
        
        # Schedule initial pass calculation
        Clock.schedule_once(self._initialize_pass_calculation, 1.0)
    
    def on_enter(self):
        """Called when entering the screen."""
        super().on_enter()
        self._start_pass_monitoring()
    
    def on_leave(self):
        """Called when leaving the screen."""
        super().on_leave()
        self._stop_pass_monitoring()
    
    def _initialize_pass_calculation(self, dt):
        """Initialize pass calculation after screen setup."""
        self.load_user_location()
        self._calculate_next_pass()
    
    def load_user_location(self):
        """Load user location from settings."""
        try:
            config_path = pathlib.Path.home() / ".mimic_data" / "location_config.json"
            if config_path.exists():
                with open(config_path, 'r') as f:
                    data = json.load(f)
                    self.user_location = (data['lat'], data['lon'])
                    log_info(f"Loaded user location: {self.user_location[0]:.4f}, {self.user_location[1]:.4f}")
            else:
                # Default to Houston if no location set
                self.user_location = (29.7604, -95.3698)
                log_info("Using default Houston location")
        except Exception as e:
            log_error(f"Failed to load user location: {e}")
            self.user_location = (29.7604, -95.3698)
    
    def set_user_location(self, lat: float, lon: float):
        """Set user location and recalculate passes."""
        self.user_location = (lat, lon)
        self._calculate_next_pass()
        log_info(f"Updated user location: {lat:.4f}, {lon:.4f}")
    
    def _calculate_next_pass(self):
        """Calculate the next ISS pass for the user's location."""
        if not self.user_location:
            log_error("No user location available for pass calculation")
            return
        
        try:
            # Load ISS TLE data
            self._load_iss_tle()
            
            if not self.iss_tle:
                log_error("Failed to load ISS TLE data")
                return
            
            # Calculate next pass
            self.next_pass_data = self._compute_next_pass()
            
            if self.next_pass_data:
                self._update_pass_display()
                self._update_sky_chart()
                log_info("Successfully calculated next ISS pass")
            else:
                log_info("No upcoming ISS passes found")
                
        except Exception as e:
            log_error(f"Failed to calculate ISS pass: {e}")
    
    def _load_iss_tle(self):
        """Load ISS TLE data from the database or online source."""
        try:
            # Try to load from database first
            db_path = pathlib.Path.home() / ".mimic_data" / "iss_telemetry.db"
            if db_path.exists():
                import sqlite3
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                
                # Get the most recent TLE data
                cursor.execute("""
                    SELECT TLE_Line1, TLE_Line2 FROM tle_data 
                    WHERE satellite_name = 'ISS (ZARYA)' 
                    ORDER BY timestamp DESC LIMIT 1
                """)
                
                result = cursor.fetchone()
                if result:
                    line1, line2 = result
                    self.iss_tle = ephem.readtle("ISS (ZARYA)", line1, line2)
                    log_info("Loaded ISS TLE from database")
                    conn.close()
                    return
                
                conn.close()
            
            # Fallback: use a recent TLE (you might want to implement online TLE fetching)
            # For now, using a sample TLE - in production, fetch from celestrak.com
            sample_tle = [
                "ISS (ZARYA)",
                "1 25544U 98067A   24001.50000000  .00012237  00000+0  22906-3 0  9994",
                "2 25544  51.6400 114.5853 0001266 288.4905 280.0644 15.50001952426048"
            ]
            self.iss_tle = ephem.readtle(*sample_tle)
            log_info("Using sample ISS TLE data")
            
        except Exception as e:
            log_error(f"Failed to load ISS TLE: {e}")
            self.iss_tle = None
    
    def _compute_next_pass(self) -> Optional[dict]:
        """Compute the next ISS pass for the user's location."""
        if not self.iss_tle or not self.user_location:
            return None
        
        try:
            # Set up observer location
            observer = ephem.Observer()
            observer.lat = str(self.user_location[0])
            observer.lon = str(self.user_location[1])
            observer.elevation = 0  # Sea level
            
            # Calculate pass times
            now = ephem.now()
            observer.date = now
            
            # Find next pass
            pass_data = self.iss_tle.next_pass(observer)
            
            if not pass_data:
                return None
            
            rise_time, rise_az, max_time, max_alt, set_time, set_az = pass_data
            
            # Convert to datetime
            rise_dt = rise_time.datetime()
            max_dt = max_time.datetime()
            set_dt = set_time.datetime()
            
            # Calculate pass duration
            duration = set_dt - rise_dt
            
            # Calculate magnitude (simplified - depends on sun position and ISS altitude)
            magnitude = self._calculate_magnitude(max_alt, max_dt)
            
            # Generate detailed pass data for sky chart
            detailed_pass = self._generate_detailed_pass_data(
                rise_time, set_time, rise_az, set_az, max_alt, max_time
            )
            
            return {
                'rise_time': rise_dt,
                'rise_azimuth': math.degrees(rise_az),
                'max_time': max_dt,
                'max_elevation': math.degrees(max_alt),
                'set_time': set_dt,
                'set_azimuth': math.degrees(set_az),
                'duration': duration,
                'magnitude': magnitude,
                'quality': self._assess_pass_quality(max_alt, duration),
                'detailed_data': detailed_pass
            }
            
        except Exception as e:
            log_error(f"Failed to compute pass: {e}")
            return None
    
    def _generate_detailed_pass_data(self, rise_time, set_time, rise_az, set_az, max_alt, max_time):
        """Generate detailed pass data for sky chart visualization."""
        try:
            # Generate points along the pass for smooth visualization
            num_points = 100
            times = []
            azimuths = []
            elevations = []
            
            observer = ephem.Observer()
            observer.lat = str(self.user_location[0])
            observer.lon = str(self.user_location[1])
            observer.elevation = 0
            
            # Calculate positions at regular intervals
            for i in range(num_points + 1):
                t = rise_time + (set_time - rise_time) * i / num_points
                observer.date = t
                
                # Compute ISS position
                self.iss_tle.compute(observer)
                
                # Get azimuth and elevation
                az = math.degrees(self.iss_tle.az)
                el = math.degrees(self.iss_tle.alt)
                
                # Only include points above horizon
                if el > 0:
                    times.append(t)
                    azimuths.append(az)
                    elevations.append(el)
            
            return {
                'times': times,
                'azimuths': azimuths,
                'elevations': elevations
            }
            
        except Exception as e:
            log_error(f"Failed to generate detailed pass data: {e}")
            return None
    
    def _calculate_magnitude(self, max_alt, max_time) -> str:
        """Calculate ISS magnitude at maximum elevation."""
        try:
            # Simplified magnitude calculation
            # ISS magnitude typically ranges from -3.9 to +1.6
            # Depends on distance, phase angle, and solar illumination
            
            # Basic calculation based on altitude and time
            alt_deg = math.degrees(max_alt)
            
            # Rough magnitude estimation
            if alt_deg > 80:
                mag = -2.0  # Very bright when overhead
            elif alt_deg > 60:
                mag = -1.5
            elif alt_deg > 40:
                mag = -1.0
            elif alt_deg > 20:
                mag = -0.5
            else:
                mag = 0.0
            
            return f"{mag:.1f}"
            
        except Exception as e:
            log_error(f"Failed to calculate magnitude: {e}")
            return "N/A"
    
    def _assess_pass_quality(self, max_alt, duration) -> str:
        """Assess the quality of the pass."""
        try:
            alt_deg = math.degrees(max_alt)
            dur_min = duration.total_seconds() / 60
            
            if alt_deg > 80 and dur_min > 5:
                return "Excellent"
            elif alt_deg > 60 and dur_min > 4:
                return "Very Good"
            elif alt_deg > 40 and dur_min > 3:
                return "Good"
            elif alt_deg > 20 and dur_min > 2:
                return "Fair"
            else:
                return "Poor"
                
        except Exception as e:
            log_error(f"Failed to assess pass quality: {e}")
            return "Unknown"
    
    def _update_pass_display(self):
        """Update the pass information display."""
        if not self.next_pass_data:
            return
        
        data = self.next_pass_data
        
        # Format times
        self.pass_start_time = data['rise_time'].strftime("%H:%M:%S")
        self.pass_end_time = data['set_time'].strftime("%H:%M:%S")
        
        # Format duration
        duration_min = int(data['duration'].total_seconds() / 60)
        duration_sec = int(data['duration'].total_seconds()) % 60
        self.pass_duration = f"{duration_min}m {duration_sec}s"
        
        # Format other values
        self.max_elevation = f"{data['max_elevation']:.1f}°"
        self.start_azimuth = f"{data['rise_azimuth']:.1f}°"
        self.end_azimuth = f"{data['set_azimuth']:.1f}°"
        self.magnitude = data['magnitude']
        self.pass_quality = data['quality']
        
        # Update status
        self._update_status(f"Next pass: {data['rise_time'].strftime('%H:%M')} - {data['set_time'].strftime('%H:%M')} (Max: {data['max_elevation']:.1f}°)")
    
    def _update_sky_chart(self):
        """Update the sky chart with the current pass data."""
        if not self.next_pass_data or not self.next_pass_data.get('detailed_data'):
            return
        
        # Find the sky chart widget
        if hasattr(self, 'ids') and 'sky_chart_container' in self.ids:
            container = self.ids.sky_chart_container
            
            # Clear existing chart
            container.clear_widgets()
            
            # Create new sky chart
            chart = SkyChartWidget()
            chart.size_hint = (1, 1)
            
            # Set the pass data
            chart.set_pass_data(
                self.next_pass_data['detailed_data'],
                self.user_location
            )
            
            container.add_widget(chart)
            self.sky_chart_widget = chart
    
    def _start_pass_monitoring(self):
        """Start monitoring for pass updates."""
        if self._pass_update_event:
            self._pass_update_event.cancel()
        
        # Update pass every 5 minutes
        self._pass_update_event = Clock.schedule_interval(self._update_pass_if_needed, 300)
    
    def _stop_pass_monitoring(self):
        """Stop monitoring for pass updates."""
        if self._pass_update_event:
            self._pass_update_event.cancel()
            self._pass_update_event = None
    
    def _update_pass_if_needed(self, dt):
        """Update pass data if needed (e.g., if current pass has ended)."""
        if not self.next_pass_data:
            return
        
        now = datetime.utcnow()
        if now > self.next_pass_data['set_time']:
            # Current pass has ended, calculate next one
            log_info("Current pass has ended, calculating next pass")
            self._calculate_next_pass()
    
    def _update_status(self, message: str):
        """Update the status label."""
        if hasattr(self, 'ids') and 'status_label' in self.ids:
            self.ids.status_label.text = message
    
    def refresh_pass_data(self):
        """Manually refresh pass data."""
        self._calculate_next_pass()
        self._update_status("Refreshing pass data...")
