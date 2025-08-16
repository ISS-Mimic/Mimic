from __future__ import annotations
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.scrollview import ScrollView
from kivy.properties import StringProperty, ListProperty
from kivy.clock import Clock
from kivy.metrics import dp
import pathlib
import sqlite3
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from kivy.lang import Builder
from ._base import MimicBase
from utils.logger import log_info, log_error

kv_path = pathlib.Path(__file__).with_name("Crew_Screen.kv")
Builder.load_file(str(kv_path))

class CrewMemberWidget(BoxLayout):
    """Individual crew member widget with photo, info, and stats."""
    
    name = StringProperty("")
    country = StringProperty("")
    spacecraft = StringProperty("")
    expedition = StringProperty("")
    mission_days = StringProperty("0")
    total_days = StringProperty("0")
    role = StringProperty("FE")
    mimic_directory = StringProperty("")
    image_url = StringProperty("")
    
    def __init__(self, crew_data: Dict, mimic_dir: str = "", **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(200)
        self.padding = dp(10)
        self.spacing = dp(5)
        
        # Store mimic directory
        self.mimic_directory = mimic_dir
        
        # Update properties
        self.name = crew_data.get('name', 'Unknown')
        self.country = crew_data.get('country', 'Unknown')
        self.spacecraft = crew_data.get('spaceship', 'Unknown')
        self.expedition = crew_data.get('expedition', 'Unknown')
        self.role = self._determine_role(crew_data)
        
        # Use actual data from database instead of hardcoded estimates
        self.mission_days = str(crew_data.get('current_mission_duration', 0))
        self.total_days = str(crew_data.get('total_time_in_space', 0))
        self.image_url = crew_data.get('image_url', '')
        
        # Debug logging for image URLs
        if self.image_url:
            log_info(f"Crew member {self.name} has image URL: {self.image_url}")
        else:
            log_info(f"Crew member {self.name} has no image URL")
        
        # Download the astronaut image if we have a URL
        if self.image_url:
            # We need to get the parent screen to call download_astronaut_image
            # For now, we'll store the URL and handle downloading in the parent
            pass
    
    def _determine_role(self, crew_data: Dict) -> str:
        """Determine crew role based on available data."""
        # Use actual position data from database if available
        position = crew_data.get('position', '')
        if position:
            # Extract role from position (e.g., "ISS-CDR" -> "CMDR", "Flight Engineer" -> "FE")
            if 'CDR' in position.upper() or 'Commander' in position:
                return "CMDR"
            elif 'Engineer' in position:
                return "FE"
            elif 'Specialist' in position:
                return "MS"
            else:
                # Return first 3 characters of position if it's short enough
                return position[:3].upper() if len(position) <= 3 else position[:3].upper()
        
        # Fallback to expedition-based logic
        if "Commander" in crew_data.get('expedition', ''):
            return "CMDR"
        return "FE"


class Crew_Screen(MimicBase):
    """Dynamic crew screen that automatically displays current ISS crew."""
    
    crew_data = ListProperty([])
    expedition_number = StringProperty("Expedition 70")
    expedition_duration = StringProperty("0 days")
    iss_crewed_years = StringProperty("24")
    iss_crewed_months = StringProperty("9")
    iss_crewed_days = StringProperty("10")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.crew_widgets = []
        self.update_timer = None
        self.poll_timer = None
        
    def on_pre_enter(self):
        """Called when screen is about to be displayed."""
        super().on_pre_enter()
        self.load_crew_data()
        self.update_iss_crewed_time()
        
        # switchable scheduling: poll fast until data appears
        if self.poll_timer:
            self.poll_timer.cancel()
        if self.update_timer:
            self.update_timer.cancel()
        if self.crew_data:
            self.update_timer = Clock.schedule_interval(self.update_crew_data, 300)
        else:
            self.poll_timer = Clock.schedule_interval(self._poll_for_crew, 2.0)
        
        # Set up expedition duration timer (updates every second)
        self.expedition_timer = Clock.schedule_interval(self.update_expedition_duration, 1.0)
    
    def on_pre_leave(self):
        """Called when screen is about to be hidden."""
        if self.update_timer:
            self.update_timer.cancel()
            self.update_timer = None
        if self.poll_timer:
            self.poll_timer.cancel()
            self.poll_timer = None
        if hasattr(self, 'expedition_timer') and self.expedition_timer:
            self.expedition_timer.cancel()
            self.expedition_timer = None
        super().on_pre_leave()
    
    def get_db_path(self) -> str:
        """Get the database path using the centralized function."""
        # Import the centralized function from GUI
        from GUI import get_db_path as central_get_db_path
        db_path = central_get_db_path('iss_crew.db')
        log_info(f"Using centralized database path: {db_path}")
        return db_path
    
    def load_crew_data(self):
        """Load crew data from the database."""
        try:
            db_path = self.get_db_path()
            log_info(f"Attempting to load crew data from: {db_path}")
            
            # Check if database file exists
            db_file = Path(db_path)
            if not db_file.exists():
                log_info(f"Database not ready yet: {db_path}")
                self.crew_data = []
                return
            
            #log_info(f"Database file exists, size: {db_file.stat().st_size} bytes")
            
            # Try to connect to database
            #log_info("Attempting to connect to database...")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            #log_info("Database connection successful")
            
            # Check what tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            #log_info(f"Available tables: {[t[0] for t in tables]}")
            
            # Get current crew members with all available fields
            cursor.execute("""
                SELECT name, country, spaceship, expedition, position, launch_date, 
                       launch_time, landing_spacecraft, landing_date, landing_time,
                       mission_duration, orbits, status, image_url, total_time_in_space, 
                       current_mission_duration
                FROM current_crew 
                ORDER BY name
            """)
            
            crew_members = cursor.fetchall()
            #log_info(f"Raw crew data from current_crew table: {crew_members}")
            
            self.crew_data = [
                {
                    'name': row[0],
                    'country': row[1],
                    'spaceship': row[2],
                    'expedition': row[3],
                    'position': row[4],
                    'launch_date': row[5],
                    'launch_time': row[6],
                    'landing_spacecraft': row[7],
                    'landing_date': row[8],
                    'landing_time': row[9],
                    'mission_duration': row[10],
                    'orbits': row[11],
                    'status': row[12],
                    'image_url': row[13],
                    'total_time_in_space': row[14],
                    'current_mission_duration': row[15]
                }
                for row in crew_members
            ]
            
            # Update expedition number from first crew member
            if self.crew_data:
                expedition = self.crew_data[0].get('expedition', '')
                if 'Expedition' in expedition:
                    self.expedition_number = expedition
                else:
                    # Extract expedition number from spacecraft info
                    self.expedition_number = self._extract_expedition_number()
            
            conn.close()
            #log_info(f"Loaded {len(self.crew_data)} crew members from database")
            
            # Update the UI
            self.update_crew_display()
            self.update_expedition_patch()
            self.update_expedition_duration()
            
        except Exception as e:
            log_error(f"Error loading crew data: {e}")
            # No fallback data needed - we'll handle empty crew gracefully
            self.crew_data = []
            self.update_crew_display()
    

    
    def format_duration_days(self, days: int) -> str:
        """
        Format duration in days to human-readable format (e.g., "2 years, 3 months, 15 days").
        """
        if days is None or days < 1:
            return "Less than 1 day"
        
        years = days // 365
        remaining_days = days % 365
        months = remaining_days // 30
        final_days = remaining_days % 30
        
        parts = []
        if years > 0:
            parts.append(f"{years} year{'s' if years != 1 else ''}")
        if months > 0:
            parts.append(f"{months} month{'s' if months != 1 else ''}")
        if final_days > 0:
            parts.append(f"{final_days} day{'s' if final_days != 1 else ''}")
        
        return ", ".join(parts) if parts else "0 days"
    
    def update_expedition_duration(self):
        """Update the expedition duration timer based on oldest crew launch date."""
        try:
            if not self.crew_data:
                self.expedition_duration = "0 days"
                return
            
            # Find the oldest launch date among current crew
            oldest_launch = None
            for crew in self.crew_data:
                launch_date = crew.get('launch_date')
                if launch_date:
                    try:
                        # Parse the launch date (YYYY-MM-DD format)
                        parsed_date = datetime.strptime(launch_date, '%Y-%m-%d')
                        if oldest_launch is None or parsed_date < oldest_launch:
                            oldest_launch = parsed_date
                    except ValueError:
                        continue
            
            if oldest_launch:
                # Calculate days since oldest launch
                today = datetime.now()
                duration_days = (today - oldest_launch).days
                self.expedition_duration = self.format_duration_days(duration_days)
            else:
                self.expedition_duration = "0 days"
                
        except Exception as e:
            log_error(f"Error updating expedition duration: {e}")
            self.expedition_duration = "0 days"
    
    def verify_image_url(self, url: str) -> bool:
        """Verify if an image URL is accessible."""
        if not url:
            return False
        
        try:
            import requests
            headers = {
                "User-Agent": "ISS-Mimic Bot (+https://github.com/ISS-Mimic; iss.mimic@gmail.com)"
            }
            response = requests.head(url, headers=headers, timeout=5)
            return response.status_code == 200
        except Exception as e:
            log_error(f"Error verifying image URL {url}: {e}")
            return False
    
    def download_astronaut_image(self, url: str, astronaut_name: str) -> str:
        """Download astronaut image and return local path."""
        if not url:
            return ""
        
        try:
            import requests
            import os
            from pathlib import Path
            
            # Create crew images directory if it doesn't exist
            crew_dir = Path(self.mimic_directory) / "Mimic" / "Pi" / "imgs" / "crew" / "astronauts"
            crew_dir.mkdir(parents=True, exist_ok=True)
            
            # Create a safe filename from astronaut name
            safe_name = "".join(c for c in astronaut_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_')
            
            # Determine file extension from URL
            if url.endswith('.jpg') or url.endswith('.jpeg'):
                ext = '.jpg'
            elif url.endswith('.png'):
                ext = '.png'
            else:
                ext = '.jpg'  # Default to jpg
            
            local_path = crew_dir / f"{safe_name}{ext}"
            
            # Download the image if it doesn't exist
            if not local_path.exists():
                headers = {
                    "User-Agent": "ISS-Mimic Bot (+https://github.com/ISS-Mimic; iss.mimic@gmail.com)"
                }
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                
                log_info(f"Downloaded astronaut image: {local_path}")
            
            return str(local_path)
            
        except Exception as e:
            log_error(f"Error downloading astronaut image from {url}: {e}")
            return ""
    
    def get_crewed_vehicles_on_orbit(self) -> List[Dict]:
        """Get information about crewed vehicles currently on orbit."""
        # This would ideally come from a database or API
        # For now, return hardcoded information
        return [
            {
                'name': 'Soyuz MS-24',
                'launch_date': '15 Sep 23',
                'crew_count': 3
            },
            {
                'name': 'SpaceX Crew-7',
                'launch_date': '26 Aug 23',
                'crew_count': 4
            }
        ]
    
    def _extract_expedition_number(self) -> str:
        """Extract expedition number from spacecraft or other data."""
        # This is a simplified approach - you might want to enhance this
        for crew in self.crew_data:
            if 'Expedition' in crew.get('expedition', ''):
                return crew['expedition']
        return "Expedition 70"  # Default fallback
    
    def update_crew_display(self):
        """Update the crew display widgets."""
        try:
            # Clear existing crew widgets
            crew_container = self.ids.crew_container
            if hasattr(crew_container, 'clear_widgets'):
                crew_container.clear_widgets()
            self.crew_widgets.clear()
            
            # Create new crew widgets
            for crew_data in self.crew_data:
                crew_widget = CrewMemberWidget(crew_data, mimic_dir=self.mimic_directory)
                crew_container.add_widget(crew_widget)
                self.crew_widgets.append(crew_widget)
            
            log_info(f"Updated crew display with {len(self.crew_data)} members")
            
        except Exception as e:
            log_error(f"Error updating crew display: {e}")
            
            # Create new crew widgets
            for crew_data in self.crew_data:
                crew_widget = CrewMemberWidget(crew_data, mimic_dir=self.mimic_directory)
                crew_container.add_widget(crew_widget)
                self.crew_widgets.append(crew_widget)
            
            log_info(f"Updated crew display with {len(self.crew_data)} members")
            
        except Exception as e:
            log_error(f"Error updating crew display: {e}")
    
    def update_iss_crewed_time(self):
        """Update the ISS crewed time display."""
        try:
            if not self.crew_data:
                self.iss_crewed_years = "0"
                self.iss_crewed_months = "0"
                self.iss_crewed_days = "0"
                return
            
            # Find the oldest launch date among current crew
            oldest_launch = None
            for crew in self.crew_data:
                launch_date = crew.get('launch_date')
                if launch_date:
                    try:
                        # Parse the launch date (YYYY-MM-DD format)
                        parsed_date = datetime.strptime(launch_date, '%Y-%m-%d')
                        if oldest_launch is None or parsed_date < oldest_launch:
                            oldest_launch = parsed_date
                    except ValueError:
                        continue
            
            if oldest_launch:
                # Calculate days since oldest launch
                now = datetime.now()
                duration = now - oldest_launch
                
                years = duration.days // 365
                remaining_days = duration.days % 365
                months = remaining_days // 30
                days = remaining_days % 30
                
                self.iss_crewed_years = str(years)
                self.iss_crewed_months = str(months)
                self.iss_crewed_days = str(days)
                
                log_info(f"Updated ISS crewed time: {years} years, {months} months, {days} days")
            
        except Exception as e:
            log_error(f"Error updating ISS crewed time: {e}")
    
    def update_crew_data(self, dt):
        """Periodic update of crew data."""
        self.load_crew_data()
        self.update_iss_crewed_time()
        self.update_crewed_vehicles_display()
    
    def refresh_crew_data(self):
        """Manual refresh of crew data."""
        log_info("Manual refresh of crew data requested")
        self.load_crew_data()
        self.update_iss_crewed_time()
        self.update_crewed_vehicles_display()
    
    def update_crewed_vehicles_display(self):
        """Update the crewed vehicles on orbit display."""
        try:
            vehicles = self.get_crewed_vehicles_from_vv_db()
            total_crew = sum(v['crew_count'] for v in vehicles)
            
            # Update the crew count display
            if hasattr(self.ids, 'total_crew_count'):
                self.ids.total_crew_count.text = str(total_crew)
            
            # Update the crewed vehicles list
            self.update_crewed_vehicles_list(vehicles)
            
            log_info(f"Updated crewed vehicles display: {len(vehicles)} vehicles, {total_crew} total crew")
            
        except Exception as e:
            log_error(f"Error updating crewed vehicles display: {e}")
    
    def get_crewed_vehicles_from_vv_db(self) -> List[Dict]:
        """Get crewed vehicles from the VV database."""
        try:
            from GUI import get_db_path
            vv_db_path = get_db_path('vv.db')
            
            log_info(f"Attempting to access VV database at: {vv_db_path}")
            
            if not Path(vv_db_path).exists():
                log_error(f"VV database not found at {vv_db_path}")
                return []
            
            log_info(f"VV database exists, size: {Path(vv_db_path).stat().st_size} bytes")
            
            conn = sqlite3.connect(vv_db_path)
            cursor = conn.cursor()
            
            # Check what tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            log_info(f"VV database tables: {[t[0] for t in tables]}")
            
            # Check if vehicles table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vehicles'")
            if not cursor.fetchone():
                log_error("Vehicles table not found in VV database")
                conn.close()
                return []
            
            # Check vehicles table structure
            cursor.execute("PRAGMA table_info(vehicles)")
            columns = cursor.fetchall()
            log_info(f"Vehicles table structure: {[col[1] for col in columns]}")
            
            # Check total vehicle count
            cursor.execute("SELECT COUNT(*) FROM vehicles")
            total_count = cursor.fetchone()[0]
            log_info(f"Total vehicles in database: {total_count}")
            
            # Check crewed vehicle count
            cursor.execute("SELECT COUNT(*) FROM vehicles WHERE Type = 'Crewed'")
            crewed_count = cursor.fetchone()[0]
            log_info(f"Crewed vehicles in database: {crewed_count}")
            
            # Get crewed vehicles
            cursor.execute("""
                SELECT Mission, Spacecraft, Arrival, Location 
                FROM vehicles 
                WHERE Type = 'Crewed' 
                ORDER BY Arrival DESC
            """)
            
            crewed_vehicles = []
            for row in cursor.fetchall():
                mission, spacecraft, arrival, location = row
                if mission and spacecraft:
                    # Estimate crew count based on spacecraft type
                    crew_count = 4 if 'Crew' in str(spacecraft) else 3  # SpaceX Crew-7 has 4, Soyuz has 3
                    
                    crewed_vehicles.append({
                        'mission': str(mission),
                        'spacecraft': str(spacecraft),
                        'arrival': str(arrival) if arrival else 'Unknown',
                        'location': str(location) if location else 'Unknown',
                        'crew_count': crew_count
                    })
            
            conn.close()
            log_info(f"Found {len(crewed_vehicles)} crewed vehicles in VV database")
            return crewed_vehicles
            
        except Exception as e:
            log_error(f"Error getting crewed vehicles from VV database: {e}")
            return []
    
    def update_crewed_vehicles_list(self, vehicles: List[Dict]):
        """Update the crewed vehicles list display."""
        try:
            crewed_container = self.ids.crewed_vehicles_container
            if not hasattr(crewed_container, 'clear_widgets'):
                return
            
            # Clear existing widgets
            crewed_container.clear_widgets()
            
            # Add vehicle widgets
            for vehicle in vehicles:
                vehicle_widget = self.create_vehicle_widget(vehicle)
                crewed_container.add_widget(vehicle_widget)
            
            log_info(f"Updated crewed vehicles list with {len(vehicles)} vehicles")
            
        except Exception as e:
            log_error(f"Error updating crewed vehicles list: {e}")
    
    def create_vehicle_widget(self, vehicle: Dict) -> BoxLayout:
        """Create a widget for displaying vehicle information."""
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.label import Label
        
        widget = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(60))
        
        # Mission name
        mission_label = Label(
            text=vehicle['mission'],
            color=(1, 1, 1, 1),
            font_size=dp(12),
            bold=True,
            size_hint_y=0.5
        )
        
        # Spacecraft and arrival info
        info_label = Label(
            text=f"{vehicle['spacecraft']}\nArrived: {vehicle['arrival']}",
            color=(0.8, 0.8, 0.8, 1),
            font_size=dp(10),
            size_hint_y=0.5
        )
        
        widget.add_widget(mission_label)
        widget.add_widget(info_label)
        
        return widget
    
    def update_expedition_patch(self):
        """Update the expedition patch image by fetching from Wikipedia."""
        try:
            if hasattr(self.ids, 'expedition_patch'):
                # Extract expedition number from expedition_number (e.g., "Expedition 73" -> "73")
                expedition_match = re.search(r'Expedition\s+(\d+)', self.expedition_number)
                if not expedition_match:
                    log_info("Could not extract expedition number, using default patch")
                    return
                
                expedition_num = expedition_match.group(1)
                log_info(f"Fetching patch for Expedition {expedition_num}")
                
                # Try to get the patch from Wikipedia
                patch_url = self.fetch_expedition_patch_from_wikipedia(expedition_num)
                if patch_url:
                    self.ids.expedition_patch.source = patch_url
                    log_info(f"Updated expedition patch to: {patch_url}")
                else:
                    log_info("Could not fetch expedition patch from Wikipedia")
                    
        except Exception as e:
            log_error(f"Error updating expedition patch: {e}")
    
    def fetch_expedition_patch_from_wikipedia(self, expedition_num: str) -> str:
        """Fetch expedition patch from Wikipedia using MediaWiki API."""
        try:
            import requests
            
            # Create cache directory for patches
            cache_dir = Path.home() / ".mimic_data" / "patches"
            cache_dir.mkdir(exist_ok=True)
            
            # Check if we already have this patch cached
            cached_patch = cache_dir / f"expedition_{expedition_num}_patch.png"
            if cached_patch.exists():
                log_info(f"Using cached patch for Expedition {expedition_num}")
                return str(cached_patch)
            
            # Try to fetch from Wikipedia MediaWiki API
            # First, get the file info from the expedition page
            expedition_page_url = f"https://en.wikipedia.org/wiki/Expedition_{expedition_num}"
            
            # Look for the patch image in the page content
            headers = {
                'User-Agent': 'ISS Mimic Bot (https://github.com/ISS-Mimic; iss.mimic@gmail.com)'
            }
            response = requests.get(expedition_page_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse the HTML to find the patch image
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for the patch image - it's usually in the infobox or near the top
            patch_img = None
            
            # Try multiple selectors to find the patch image
            selectors = [
                'img[src*="ISS_Expedition"]',
                'img[src*="Expedition"]',
                'img[src*="patch"]',
                'img[src*="Patch"]'
            ]
            
            for selector in selectors:
                patch_img = soup.select_one(selector)
                if patch_img and 'patch' in patch_img.get('src', '').lower():
                    break
            
            if not patch_img:
                log_info(f"No patch image found on Expedition {expedition_num} page")
                return ""
            
            # Get the image URL
            img_src = patch_img.get('src')
            if not img_src:
                return ""
            
            # Convert to full URL if it's relative
            if img_src.startswith('//'):
                img_url = 'https:' + img_src
            elif img_src.startswith('/'):
                img_url = 'https://en.wikipedia.org' + img_src
            else:
                img_url = img_src
            
            log_info(f"Found patch image URL: {img_url}")
            
            # Download the image
            img_response = requests.get(img_url, headers=headers, timeout=15)
            img_response.raise_for_status()
            
            # Save to cache
            with open(cached_patch, 'wb') as f:
                f.write(img_response.content)
            
            log_info(f"Downloaded and cached patch for Expedition {expedition_num}")
            return str(cached_patch)
            
        except Exception as e:
            log_error(f"Error fetching expedition patch from Wikipedia: {e}")
            return ""
    
    def get_crew_statistics(self) -> Dict:
        """Get statistics about the current crew."""
        try:
            if not self.crew_data:
                return {}
            
            countries = [crew['country'] for crew in self.crew_data]
            spacecraft = [crew['spaceship'] for crew in self.crew_data]
            
            stats = {
                'total_crew': len(self.crew_data),
                'countries': list(set(countries)),
                'spacecraft': list(set(spacecraft)),
                'expedition': self.expedition_number,
                'longest_mission': max(int(crew.get('mission_days', 0)) for crew in self.crew_data) if self.crew_data else 0
            }
            
            return stats
            
        except Exception as e:
            log_error(f"Error calculating crew statistics: {e}")
            return {}

    def _poll_for_crew(self, dt):
        """Fast polling until crew data is available, then switch to normal interval."""
        prev_count = len(self.crew_data)
        self.load_crew_data()
        if self.crew_data and len(self.crew_data) != prev_count:
            # first time data appears: stop polling, switch to normal interval
            if self.poll_timer:
                self.poll_timer.cancel()
                self.poll_timer = None
            if not self.update_timer:
                self.update_timer = Clock.schedule_interval(self.update_crew_data, 300)
            # kick vehicles update shortly after
            Clock.schedule_once(lambda _dt: self.update_crewed_vehicles_display(), 1.0)
