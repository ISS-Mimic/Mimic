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

# Don't import matplotlib at module level - import it only when needed
MATPLOTLIB_AVAILABLE = None  # Will be set to True/False when first needed
import io
# Safe numpy import
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("Orbit Pass: Numpy not available, some features may be limited")

from ._base import MimicBase
from utils.logger import log_info, log_error

kv_path = pathlib.Path(__file__).with_name("Orbit_Pass.kv")
Builder.load_file(str(kv_path))


def _safe_import_matplotlib():
    """Safely import matplotlib and set availability flag."""
    global MATPLOTLIB_AVAILABLE
    
    if MATPLOTLIB_AVAILABLE is not None:
        return MATPLOTLIB_AVAILABLE
    
    try:
        log_info("Orbit Pass: Attempting to import matplotlib...")
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        
        # Test if it actually works
        fig, ax = plt.subplots(figsize=(1, 1))
        plt.close(fig)
        
        MATPLOTLIB_AVAILABLE = True
        log_info("Orbit Pass: Matplotlib imported successfully and tested")
        return True
        
    except Exception as e:
        log_error(f"Orbit Pass: Failed to import matplotlib: {e}")
        import traceback
        traceback.print_exc()
        MATPLOTLIB_AVAILABLE = False
        return False


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
        
        # Check if matplotlib is available
        if not _safe_import_matplotlib():
            log_error("Orbit Pass: Matplotlib not available, showing fallback")
            # Show a simple colored rectangle as fallback
            with self.canvas:
                Color(0.2, 0.2, 0.2, 1)
                Rectangle(pos=self.pos, size=self.size)
            return
        
        try:
            # Import matplotlib modules locally
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_agg import FigureCanvasAgg
            
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
                # Handle numpy availability
                if NUMPY_AVAILABLE:
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
                else:
                    # Fallback without numpy
                    az_rad = [math.radians(az) for az in self.pass_data['azimuths']]
                    el = self.pass_data['elevations']
                    
                    # Plot the pass arc
                    ax.plot(az_rad, el, 'r-', linewidth=3, label='ISS Pass')
                    
                    # Mark key points
                    if len(el) > 0:
                        max_el_idx = el.index(max(el))
                        ax.plot(az_rad[max_el_idx], el[max_el_idx], 'ro', markersize=8, label='Max Elevation')
                        
                        # Mark start and end points
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
            log_info("Orbit Pass: Sky chart created successfully")
            
        except Exception as e:
            log_error(f"Orbit Pass: Failed to create sky chart: {e}")
            import traceback
            traceback.print_exc()
            # Show a simple colored rectangle as fallback
            with self.canvas:
                Color(0.2, 0.2, 0.2, 1)
                Rectangle(pos=self.pos, size=self.size)


class Orbit_Pass(MimicBase):
    """Screen for displaying ISS pass predictions and sky charts."""
    
    # UI scaling property for responsive design
    ui_scale = NumericProperty(1.0)
    
    # Properties for pass information
    pass_start_time = StringProperty("--:--:--")
    pass_end_time = StringProperty("--:--:--")
    pass_duration = StringProperty("--:--")
    max_elevation = StringProperty("--°")
    start_azimuth = StringProperty("--°")
    end_azimuth = StringProperty("--°")
    magnitude = StringProperty("--.-")
    pass_quality = StringProperty("--")
    
    def __init__(self, **kwargs):
        # Initialize basic attributes first
        self.user_location = None
        self.iss_tle = None
        self.next_pass_data = None
        self.sky_chart_widget = None
        self._pass_update_event = None
        
        try:
            super().__init__(**kwargs)
            log_info("Orbit Pass: Screen initialized successfully")
            
            # Schedule initial pass calculation
            Clock.schedule_once(self._initialize_pass_calculation, 1.0)
            
        except Exception as e:
            log_error(f"Orbit Pass: Failed to initialize screen: {e}")
            import traceback
            traceback.print_exc()
            # Set default location if initialization failed
            self.user_location = (29.7604, -95.3698)  # Default Houston
            log_info("Orbit Pass: Basic initialization completed after error")
    
    def on_enter(self):
        """Called when entering the screen."""
        log_info("Orbit Pass: Screen entered")
        try:
            super().on_enter()
            self._start_pass_monitoring()
            log_info("Orbit Pass: Screen entry completed successfully")
        except Exception as e:
            log_error(f"Orbit Pass: Screen entry failed: {e}")
            import traceback
            traceback.print_exc()
    
    def on_leave(self):
        """Called when leaving the screen."""
        log_info("Orbit Pass: Screen leaving")
        try:
            super().on_leave()
            self._stop_pass_monitoring()
            log_info("Orbit Pass: Screen leave completed successfully")
        except Exception as e:
            log_error(f"Orbit Pass: Screen leave failed: {e}")
            import traceback
            traceback.print_exc()
    
    def on_size(self, *args):
        """Handle screen size changes for UI scaling."""
        try:
            # Scale typography across devices; 1280px baseline
            self.ui_scale = max(0.8, min(2.0, self.width / 1280.0))
        except Exception:
            self.ui_scale = 1.0
    
    def _initialize_pass_calculation(self, dt):
        """Initialize pass calculation after screen setup."""
        log_info("Orbit Pass: Starting initialization...")
        try:
            self.load_user_location()
            log_info("Orbit Pass: Location loaded, calculating next pass...")
            self._calculate_next_pass()
            log_info("Orbit Pass: Initialization complete")
        except Exception as e:
            log_error(f"Orbit Pass: Initialization failed: {e}")
            import traceback
            traceback.print_exc()
    
    def load_user_location(self):
        """Load user location from settings."""
        log_info("Orbit Pass: Loading user location...")
        try:
            config_path = pathlib.Path.home() / ".mimic_data" / "location_config.json"
            log_info(f"Orbit Pass: Looking for config at: {config_path}")
            
            if config_path.exists():
                log_info("Orbit Pass: Config file found, reading...")
                with open(config_path, 'r') as f:
                    data = json.load(f)
                    self.user_location = (data['lat'], data['lon'])
                    log_info(f"Orbit Pass: Loaded user location: {self.user_location[0]:.4f}, {self.user_location[1]:.4f}")
            else:
                # Default to Houston if no location set
                log_info("Orbit Pass: No config file found, using default Houston location")
                self.user_location = (29.7604, -95.3698)
                log_info("Orbit Pass: Default location set: 29.7604, -95.3698")
        except Exception as e:
            log_error(f"Orbit Pass: Failed to load user location: {e}")
            import traceback
            traceback.print_exc()
            self.user_location = (29.7604, -95.3698)
            log_info("Orbit Pass: Fallback to default location due to error")
    
    def set_user_location(self, lat: float, lon: float):
        """Set user location and recalculate passes."""
        log_info(f"Orbit Pass: Setting user location to: {lat:.4f}, {lon:.4f}")
        self.user_location = (lat, lon)
        log_info("Orbit Pass: Location set, recalculating passes...")
        self._calculate_next_pass()
        log_info(f"Orbit Pass: User location updated and passes recalculated")
    
    def _calculate_next_pass(self):
        """Calculate the next ISS pass for the user's location."""
        log_info("Orbit Pass: Starting pass calculation...")
        
        if not self.user_location:
            log_error("Orbit Pass: No user location available for pass calculation")
            self._update_status("Error: No location set")
            return
        
        log_info(f"Orbit Pass: Using location: {self.user_location[0]:.4f}, {self.user_location[1]:.4f}")
        
        try:
            self._update_status("Loading ISS orbital data...")
            log_info("Orbit Pass: Loading ISS TLE data...")
            
            # Load ISS TLE data
            self._load_iss_tle()
            
            if not self.iss_tle:
                log_error("Orbit Pass: Failed to load ISS TLE data")
                self._update_status("Error: Failed to load orbital data")
                return
            
            log_info("Orbit Pass: TLE data loaded successfully")
            self._update_status("Calculating next pass...")
            log_info("Orbit Pass: Computing next pass...")
            
            # Calculate next pass
            self.next_pass_data = self._compute_next_pass()
            
            if self.next_pass_data:
                log_info("Orbit Pass: Pass data computed successfully")
                log_info(f"Orbit Pass: Pass details - Start: {self.next_pass_data['rise_time']}, End: {self.next_pass_data['set_time']}")
                
                self._update_pass_display()
                log_info("Orbit Pass: Pass display updated")
                
                self._update_sky_chart()
                log_info("Orbit Pass: Sky chart updated")
                
                log_info("Orbit Pass: Successfully calculated next ISS pass")
                self._update_status(f"Pass calculated: {self.next_pass_data['rise_time'].strftime('%H:%M')} - {self.next_pass_data['set_time'].strftime('%H:%M')} (Max: {self.next_pass_data['max_elevation']:.1f}°)")
            else:
                log_info("Orbit Pass: No upcoming ISS passes found")
                self._update_status("No upcoming passes found - try refreshing")
                
        except Exception as e:
            log_error(f"Orbit Pass: Failed to calculate ISS pass: {e}")
            self._update_status(f"Error: {str(e)[:50]}...")
            import traceback
            traceback.print_exc()
    
    def _load_iss_tle(self):
        """Load ISS TLE data from database or fallback."""
        log_info("Orbit Pass: Starting TLE loading process...")
        try:
            # Try to load from database first
            db_path = pathlib.Path.home() / ".mimic_data" / "iss_telemetry.db"
            log_info(f"Orbit Pass: Looking for database at: {db_path}")
            
            if db_path.exists():
                log_info("Orbit Pass: Database found, attempting to read TLE data...")
                import sqlite3
                
                try:
                    conn = sqlite3.connect(str(db_path))
                    cursor = conn.cursor()
                    
                    log_info("Orbit Pass: Executing SQL query for TLE data...")
                    cursor.execute("SELECT tle_line1, tle_line2 FROM tle_data WHERE satellite_name = 'ISS' ORDER BY epoch_date DESC LIMIT 1")
                    result = cursor.fetchone()
                    
                    if result:
                        tle_line1, tle_line2 = result
                        log_info("Orbit Pass: TLE data found in database")
                        self.iss_tle = ephem.readtle("ISS", tle_line1, tle_line2)
                        log_info("Orbit Pass: TLE data parsed successfully")
                        conn.close()
                        return
                    else:
                        log_info("Orbit Pass: No TLE data found in database")
                        conn.close()
                        
                except Exception as e:
                    log_error(f"Orbit Pass: Database read failed: {e}")
                    if 'conn' in locals():
                        conn.close()
            
            # Fallback to sample TLE data
            log_info("Orbit Pass: Using fallback TLE data...")
            sample_tle = [
                "ISS (ZARYA)",
                "1 25544U 98067A   24150.50000000  .00012287  00000+0  22952-3 0  9994",
                "2 25544  51.6400 114.6000 0001000 330.5000 280.0000 15.50000000 00000"
            ]
            
            try:
                log_info("Orbit Pass: Attempting to parse sample TLE...")
                self.iss_tle = ephem.readtle(*sample_tle)
                log_info("Orbit Pass: Sample TLE parsed successfully")
            except Exception as e:
                log_error(f"Orbit Pass: Failed to parse sample TLE: {e}")
                log_info("Orbit Pass: Creating basic EarthSatellite object as fallback...")
                # Create a basic satellite object as last resort
                self.iss_tle = ephem.EarthSatellite()
                self.iss_tle.name = "ISS"
                log_info("Orbit Pass: Basic EarthSatellite object created successfully")
                
        except Exception as e:
            log_error(f"Orbit Pass: TLE loading failed: {e}")
            import traceback
            traceback.print_exc()
            # Create a basic satellite object as last resort
            self.iss_tle = ephem.EarthSatellite()
            self.iss_tle.name = "ISS"
    
    def _compute_next_pass(self):
        """Compute the next ISS pass for the current location."""
        log_info("Orbit Pass: Starting pass computation...")
        try:
            if not self.iss_tle or not self.user_location:
                log_error("Orbit Pass: Missing TLE data or user location")
                return None
            
            log_info(f"Orbit Pass: Using location: {self.user_location[0]:.4f}, {self.user_location[1]:.4f}")
            
            # Set up observer
            observer = ephem.Observer()
            observer.lat = str(self.user_location[0])
            observer.lon = str(self.user_location[1])
            observer.elevation = 0
            
            # Get current time
            now = datetime.utcnow()
            observer.date = now
            log_info(f"Orbit Pass: Current time (UTC): {now}")
            
            # For now, generate a sample pass for testing
            log_info("Orbit Pass: Generating sample pass data...")
            sample_pass = self._generate_sample_pass_data(now)
            
            if sample_pass:
                log_info("Orbit Pass: Sample pass data created successfully")
                log_info(f"Orbit Pass: Pass details - Start: {sample_pass['rise_time'].strftime('%H:%M')}, End: {sample_pass['set_time'].strftime('%H:%M')}, Duration: {sample_pass['duration']}")
                return sample_pass
            else:
                log_error("Orbit Pass: Failed to generate sample pass data")
                return None
                
        except Exception as e:
            log_error(f"Orbit Pass: Pass computation failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _generate_sample_pass_data(self, base_time):
        """Generate sample pass data for testing purposes."""
        log_info("Orbit Pass: Starting sample pass data generation...")
        try:
            # Create a sample pass starting 2 hours from now
            rise_time = base_time + timedelta(hours=2)
            max_time = rise_time + timedelta(minutes=2, seconds=30)
            set_time = rise_time + timedelta(minutes=5)
            
            log_info(f"Orbit Pass: Sample pass times - Rise: {rise_time}, Max: {max_time}, Set: {set_time}")
            
            # Generate detailed pass data
            log_info("Orbit Pass: Generating detailed pass data...")
            detailed_data = self._generate_detailed_pass_data(rise_time, set_time, 245.0, 114.0, 67.2, max_time)
            
            if detailed_data:
                log_info(f"Orbit Pass: Generated {len(detailed_data['azimuths'])} points for sky chart")
                log_info(f"Orbit Pass: Azimuth range: {detailed_data['azimuths'][0]:.1f}° to {detailed_data['azimuths'][-1]:.1f}°")
                log_info(f"Orbit Pass: Elevation range: {detailed_data['elevations'][0]:.1f}° to {detailed_data['elevations'][-1]:.1f}°")
                
                # Calculate pass quality and magnitude
                magnitude = self._calculate_magnitude(67.2, max_time)
                quality = self._assess_pass_quality(67.2, timedelta(minutes=5))
                
                log_info("Orbit Pass: Sample pass data generation completed successfully")
                
                return {
                    'rise_time': rise_time,
                    'set_time': set_time,
                    'max_elevation': 67.2,
                    'max_elevation_time': max_time,
                    'duration': timedelta(minutes=5),
                    'start_azimuth': 245.0,
                    'end_azimuth': 114.0,
                    'magnitude': magnitude,
                    'quality': quality,
                    'detailed_data': detailed_data
                }
            else:
                log_error("Orbit Pass: Failed to generate detailed pass data")
                return None
                
        except Exception as e:
            log_error(f"Orbit Pass: Sample pass generation failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _generate_detailed_pass_data(self, rise_time, set_time, rise_az, set_az, max_alt, max_time):
        """Generate detailed pass data for sky chart visualization."""
        try:
            # Generate points along the pass for smooth visualization
            num_points = 50
            times = []
            azimuths = []
            elevations = []
            
            # Create a smooth pass arc
            for i in range(num_points + 1):
                t = i / num_points
                
                # Interpolate azimuth (handle crossing 0°/360°)
                if abs(rise_az - set_az) > 180:
                    if rise_az < set_az:
                        rise_az += 360
                    else:
                        set_az += 360
                
                az = rise_az + (set_az - rise_az) * t
                if az > 360:
                    az -= 360
                
                # Create elevation curve (bell shape)
                if t <= 0.5:
                    # Rising phase
                    elev = max_alt * (2 * t)
                else:
                    # Setting phase
                    elev = max_alt * (2 * (1 - t))
                
                # Ensure elevation is positive
                elev = max(0, elev)
                
                times.append(rise_time + (set_time - rise_time) * t)
                azimuths.append(az)
                elevations.append(elev)
            
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
            alt_deg = max_alt
            
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
            alt_deg = max_alt
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
        log_info("Orbit Pass: Starting pass display update...")
        
        if not self.next_pass_data:
            log_error("Orbit Pass: No pass data available for display update")
            return
        
        data = self.next_pass_data
        log_info(f"Orbit Pass: Updating display with pass data: {data['rise_time']} to {data['set_time']}")
        
        try:
            # Update time displays
            start_time = data['rise_time'].strftime('%H:%M:%S')
            end_time = data['set_time'].strftime('%H:%M:%S')
            log_info(f"Orbit Pass: Formatted times - Start: {start_time}, End: {end_time}")
            
            # Calculate duration
            duration = data['set_time'] - data['rise_time']
            duration_str = f"{int(duration.total_seconds() // 60)}m {int(duration.total_seconds() % 60)}s"
            log_info(f"Orbit Pass: Formatted duration: {duration_str}")
            
            # Update properties
            self.pass_start_time = start_time
            self.pass_end_time = end_time
            self.pass_duration = duration_str
            self.max_elevation = f"{data['max_elevation']:.1f}°"
            self.start_azimuth = f"{data['start_azimuth']:.1f}°"
            self.end_azimuth = f"{data['end_azimuth']:.1f}°"
            self.magnitude = data['magnitude']
            self.pass_quality = data['quality']
            
            log_info(f"Orbit Pass: Formatted values - Max Elev: {self.max_elevation}, Start Az: {self.start_azimuth}, End Az: {self.end_azimuth}")
            log_info(f"Orbit Pass: Formatted values - Magnitude: {self.magnitude}, Quality: {self.pass_quality}")
            
            # Update status
            self._update_status(f"Next pass: {start_time} - {end_time} (Max: {self.max_elevation})")
            log_info(f"Orbit Pass: Status updated: {self.status_text}")
            
            log_info("Orbit Pass: Pass display update completed successfully")
            
        except Exception as e:
            log_error(f"Orbit Pass: Failed to update pass display: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_sky_chart(self):
        """Update the sky chart with the current pass data."""
        log_info("Orbit Pass: Starting sky chart update...")
        
        if not self.next_pass_data or not self.next_pass_data.get('detailed_data'):
            log_error("Orbit Pass: No pass data available for sky chart")
            return
        
        # Find the sky chart widget
        if hasattr(self, 'ids') and 'sky_chart_container' in self.ids:
            container = self.ids.sky_chart_container
            log_info("Orbit Pass: Found sky chart container")
            
            # Clear existing chart
            container.clear_widgets()
            log_info("Orbit Pass: Cleared existing chart widgets")
            
            try:
                # Create new sky chart
                log_info("Orbit Pass: Creating new SkyChartWidget...")
                chart = SkyChartWidget()
                chart.size_hint = (1, 1)
                
                # Set the pass data
                log_info("Orbit Pass: Setting pass data on chart...")
                chart.set_pass_data(
                    self.next_pass_data['detailed_data'],
                    self.user_location
                )
                
                log_info("Orbit Pass: Adding chart to container...")
                container.add_widget(chart)
                self.sky_chart_widget = chart
                log_info("Orbit Pass: Sky chart updated successfully")
                
            except Exception as e:
                log_error(f"Orbit Pass: Failed to create sky chart: {e}")
                import traceback
                traceback.print_exc()
                # Add a fallback label with more detailed information
                log_info("Orbit Pass: Adding detailed fallback label...")
                self._create_fallback_chart(container)
        else:
            log_error("Orbit Pass: Sky chart container not found in ids")
    
    def _create_fallback_chart(self, container):
        """Create a simple text-based fallback chart when matplotlib fails."""
        try:
            from kivy.uix.label import Label
            from kivy.uix.boxlayout import BoxLayout
            
            # Create a simple text representation of the pass
            if self.next_pass_data and 'detailed_data' in self.next_pass_data:
                data = self.next_pass_data['detailed_data']
                
                # Create a simple ASCII-style chart
                chart_text = "ISS Pass Chart (Text Mode)\n"
                chart_text += "=" * 30 + "\n"
                chart_text += f"Start: {self.pass_start_time}\n"
                chart_text += f"End: {self.pass_end_time}\n"
                chart_text += f"Max Elevation: {self.max_elevation}\n"
                chart_text += f"Duration: {self.pass_duration}\n"
                chart_text += f"Quality: {self.pass_quality}\n"
                chart_text += f"Magnitude: {self.magnitude}\n"
                chart_text += "\nPass Arc:\n"
                
                if 'azimuths' in data and 'elevations' in data:
                    # Show a few key points
                    num_points = len(data['azimuths'])
                    if num_points > 0:
                        chart_text += f"Start: {data['azimuths'][0]:.1f}° → {data['elevations'][0]:.1f}°\n"
                        mid_idx = num_points // 2
                        chart_text += f"Mid: {data['azimuths'][mid_idx]:.1f}° → {data['elevations'][mid_idx]:.1f}°\n"
                        chart_text += f"End: {data['azimuths'][-1]:.1f}° → {data['elevations'][-1]:.1f}°\n"
                
                chart_text += "\n(Matplotlib chart generation failed)"
                
                fallback_label = Label(
                    text=chart_text,
                    color=(1, 1, 1, 1),
                    font_size=min(20, self.height * 0.3),
                    halign='center',
                    valign='middle',
                    text_size=(self.width * 0.9, None)
                )
                fallback_label.bind(size=lambda s, size: setattr(s, 'text_size', (size[0] * 0.9, None)))
                container.add_widget(fallback_label)
                log_info("Orbit Pass: Added detailed fallback chart")
            else:
                # Simple fallback if no data
                fallback_label = Label(
                    text="Sky Chart\n(Chart generation failed)\n\nPass data loaded successfully!",
                    color=(1, 1, 1, 1),
                    font_size=20,
                    halign='center',
                    valign='middle'
                )
                fallback_label.bind(size=lambda s, size: setattr(s, 'text_size', size))
                container.add_widget(fallback_label)
                log_info("Orbit Pass: Added simple fallback label")
                
        except Exception as e:
            log_error(f"Orbit Pass: Failed to create fallback chart: {e}")
            import traceback
            traceback.print_exc()
            # Last resort - just show an error message
            try:
                from kivy.uix.label import Label
                error_label = Label(
                    text="Chart Error\nCheck logs",
                    color=(1, 0, 0, 1),
                    font_size=20
                )
                container.add_widget(error_label)
                log_info("Orbit Pass: Added error label as last resort")
            except:
                log_error("Orbit Pass: Complete failure in fallback chart creation")
    
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
        log_info(f"Orbit Pass: Updating status: {message}")
        try:
            if hasattr(self, 'ids') and 'status_label' in self.ids:
                self.ids.status_label.text = message
                log_info(f"Orbit Pass: Status label updated successfully")
            else:
                log_error("Orbit Pass: Status label not found in ids")
        except Exception as e:
            log_error(f"Orbit Pass: Failed to update status: {e}")
            import traceback
            traceback.print_exc()
    
    def refresh_pass_data(self):
        """Manually refresh pass data."""
        log_info("Orbit Pass: Manual refresh requested")
        try:
            self._update_status("Refreshing pass data...")
            self._calculate_next_pass()
            log_info("Orbit Pass: Manual refresh completed")
        except Exception as e:
            log_error(f"Orbit Pass: Manual refresh failed: {e}")
            import traceback
            traceback.print_exc()
    
    def update_location(self):
        """Update location from settings and recalculate passes."""
        log_info("Orbit Pass: Location update requested")
        try:
            self._update_status("Updating location...")
            self.load_user_location()
            self._calculate_next_pass()
            log_info("Orbit Pass: Location update completed")
        except Exception as e:
            log_error(f"Orbit Pass: Location update failed: {e}")
            import traceback
            traceback.print_exc()
