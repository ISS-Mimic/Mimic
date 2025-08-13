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
        
        # Calculate mission duration using actual launch dates
        self.mission_days = str(self._calculate_mission_days(crew_data))
        self.total_days = self._calculate_total_days(crew_data)
    
    def _determine_role(self, crew_data: Dict) -> str:
        """Determine crew role based on available data."""
        # This is a simplified approach - in reality you'd need more data
        if "Commander" in crew_data.get('expedition', ''):
            return "CMDR"
        return "FE"
    
    def _calculate_mission_days(self, crew_data: Dict) -> int:
        """Calculate days on current mission."""
        # Get the parent screen to access the mission duration calculation
        parent_screen = self.parent
        while parent_screen and not hasattr(parent_screen, 'calculate_mission_duration'):
            parent_screen = parent_screen.parent
        
        if parent_screen and hasattr(parent_screen, 'calculate_mission_duration'):
            spacecraft = crew_data.get('spaceship', '')
            return parent_screen.calculate_mission_duration(spacecraft)
        
        # Fallback to estimates if parent screen not found
        spacecraft = crew_data.get('spaceship', '').lower()
        if 'spacex crew-7' in spacecraft:
            return 152  # Launched Aug 26, 2023
        elif 'soyuz ms-24' in spacecraft:
            return 126  # Launched Sep 15, 2023
        elif 'spacex crew-8' in spacecraft:
            return 52   # Launched Mar 3, 2024
        else:
            return 100  # Default estimate
    
    def _calculate_total_days(self, crew_data: Dict) -> str:
        """Calculate total days in space across all missions."""
        # This is a placeholder - you'd need actual mission history
        # For now, return reasonable estimates based on crew member
        name = crew_data.get('name', '').lower()
        
        # Estimate based on known crew members
        if 'moghbeli' in name:
            return "277"  # First mission
        elif 'borisov' in name:
            return "215"  # First mission
        elif 'chub' in name:
            return "483"  # Multiple missions
        elif 'mogensen' in name:
            return "415"  # Multiple missions
        elif 'kononenko' in name:
            return "834"  # Multiple missions
        elif "o'hara" in name:
            return "126"  # First mission
        elif 'furukawa' in name:
            return "206"  # Multiple missions
        else:
            return "200"  # Default estimate

class Crew_Screen(MimicBase):
    """Dynamic crew screen that automatically displays current ISS crew."""
    
    crew_data = ListProperty([])
    expedition_number = StringProperty("Expedition 70")
    expedition_duration = StringProperty("00:00:00")
    iss_crewed_years = StringProperty("24")
    iss_crewed_months = StringProperty("9")
    iss_crewed_days = StringProperty("10")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.crew_widgets = []
        self.update_timer = None
        
    def on_pre_enter(self):
        """Called when screen is about to be displayed."""
        super().on_pre_enter()
        self.load_crew_data()
        self.update_iss_crewed_time()
        
        # Set up periodic updates
        if self.update_timer:
            self.update_timer.cancel()
        self.update_timer = Clock.schedule_interval(self.update_crew_data, 60)  # Update every 1 minute
        
        # Set up expedition duration timer (updates every second)
        self.expedition_timer = Clock.schedule_interval(self.update_expedition_duration, 1.0)
    
    def on_pre_leave(self):
        """Called when screen is about to be hidden."""
        if self.update_timer:
            self.update_timer.cancel()
            self.update_timer = None
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
                log_error(f"Database file does not exist: {db_path}")
                raise FileNotFoundError(f"Database not found: {db_path}")
            
            log_info(f"Database file exists, size: {db_file.stat().st_size} bytes")
            
            # Try to connect to database
            log_info("Attempting to connect to database...")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            log_info("Database connection successful")
            
            # Check what tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            log_info(f"Available tables: {[t[0] for t in tables]}")
            
            # Get current crew members
            cursor.execute("""
                SELECT name, country, spaceship, expedition 
                FROM current_crew 
                ORDER BY name
            """)
            
            crew_members = cursor.fetchall()
            log_info(f"Raw crew data from current_crew table: {crew_members}")
            
            self.crew_data = [
                {
                    'name': row[0],
                    'country': row[1],
                    'spaceship': row[2],
                    'expedition': row[3]
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
            log_info(f"Loaded {len(self.crew_data)} crew members from database")
            
            # Update the UI
            self.update_crew_display()
            self.update_expedition_patch()
            
        except Exception as e:
            log_error(f"Error loading crew data: {e}")
            # Fallback to sample data for development
            self.crew_data = [
                {'name': 'Moghbeli', 'country': 'USA', 'spaceship': 'SpaceX Crew-7', 'expedition': 'Expedition 70'},
                {'name': 'Borisov', 'country': 'Russia', 'spaceship': 'Soyuz MS-24', 'expedition': 'Expedition 70'},
                {'name': 'Chub', 'country': 'Russia', 'spaceship': 'Soyuz MS-24', 'expedition': 'Expedition 70'},
                {'name': 'Mogensen', 'country': 'Denmark', 'spaceship': 'SpaceX Crew-7', 'expedition': 'Expedition 70'},
                {'name': 'Kononenko', 'country': 'Russia', 'spaceship': 'Soyuz MS-24', 'expedition': 'Expedition 70'},
                {'name': "O'Hara", 'country': 'USA', 'spaceship': 'SpaceX Crew-7', 'expedition': 'Expedition 70'},
                {'name': 'Furukawa', 'country': 'Japan', 'spaceship': 'SpaceX Crew-7', 'expedition': 'Expedition 70'}
            ]
            self.update_crew_display()
    
    def get_spacecraft_launch_date(self, spacecraft: str) -> datetime:
        """Get launch date for a specific spacecraft."""
        # This would ideally come from a database or API
        # For now, return hardcoded launch dates
        launch_dates = {
            'SpaceX Crew-7': datetime(2023, 8, 26),
            'Soyuz MS-24': datetime(2023, 9, 15),
            'SpaceX Crew-8': datetime(2024, 3, 3),
            'Soyuz MS-25': datetime(2024, 3, 21),
        }
        
        return launch_dates.get(spacecraft, datetime.now())
    
    def calculate_mission_duration(self, spacecraft: str) -> int:
        """Calculate days since spacecraft launch."""
        try:
            launch_date = self.get_spacecraft_launch_date(spacecraft)
            duration = datetime.now() - launch_date
            return duration.days
        except:
            return 0
    
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
            
            # Create new crew widgets
            for crew_data in self.crew_data:
                crew_widget = CrewMemberWidget(crew_data, mimic_dir=self.mimic_directory)
                crew_container.add_widget(crew_widget)
                self.crew_widgets.append(crew_widget)
            
            log_info(f"Updated crew display with {len(self.crew_data)} members")
            
        except Exception as e:
            log_error(f"Error updating crew display: {e}")
    
    def update_iss_crewed_time(self):
        """Update the ISS continuously crewed time display."""
        try:
            # Calculate time since ISS became continuously crewed
            # ISS Expedition 1 began on November 2, 2000
            expedition_start = datetime(2000, 11, 2)
            now = datetime.now()
            duration = now - expedition_start
            
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
        log_info("Automatic crew data update triggered")
        self.load_crew_data()
        self.update_iss_crewed_time()
        self.update_crewed_vehicles_display()
        log_info("Automatic crew data update completed")
    

    
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
                    
                    # Format arrival date to show only the date part (YYYY-MM-DD)
                    arrival_date = 'Unknown'
                    if arrival:
                        try:
                            # If arrival is already a datetime object, format it
                            if hasattr(arrival, 'strftime'):
                                arrival_date = arrival.strftime('%Y-%m-%d')
                            else:
                                # If it's a string, try to parse it and format
                                arrival_str = str(arrival)
                                if ' ' in arrival_str:  # Contains time component
                                    arrival_date = arrival_str.split(' ')[0]  # Take just the date part
                                else:
                                    arrival_date = arrival_str
                        except Exception as e:
                            log_error(f"Error formatting arrival date '{arrival}': {e}")
                            arrival_date = 'Unknown'
                    
                    crewed_vehicles.append({
                        'mission': str(mission),
                        'spacecraft': str(spacecraft),
                        'arrival': arrival_date,
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
    
    def update_expedition_duration(self, dt):
        """Update the expedition duration timer every second."""
        try:
            # Calculate time since expedition started
            # Try to get the earliest launch date from current crew
            expedition_start = None
            
            if self.crew_data:
                # Find the earliest launch date among current crew
                for crew in self.crew_data:
                    spacecraft = crew.get('spaceship', '')
                    if spacecraft:
                        launch_date = self.get_spacecraft_launch_date(spacecraft)
                        if expedition_start is None or launch_date < expedition_start:
                            expedition_start = launch_date
            
            # Fallback to a reasonable default if no crew data
            if expedition_start is None:
                expedition_start = datetime(2024, 3, 3)  # Example: Expedition 73 start
            
            now = datetime.now()
            duration = now - expedition_start
            
            # Format as HH:MM:SS
            total_seconds = int(duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            self.expedition_duration = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            # Log every minute to show the timer is working
            if seconds == 0:
                log_info(f"Expedition duration updated: {self.expedition_duration}")
            
        except Exception as e:
            log_error(f"Error updating expedition duration: {e}")
            self.expedition_duration = "00:00:00"
