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
    
    def __init__(self, crew_data: Dict, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(200)
        self.padding = dp(10)
        self.spacing = dp(5)
        
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
        self.update_timer = Clock.schedule_interval(self.update_crew_data, 300)  # Update every 5 minutes
    
    def on_pre_leave(self):
        """Called when screen is about to be hidden."""
        if self.update_timer:
            self.update_timer.cancel()
            self.update_timer = None
        super().on_pre_leave()
    
    def get_db_path(self) -> str:
        """Get the database path, prioritizing /dev/shm on Linux."""
        if Path("/dev/shm").exists() and Path("/dev/shm").is_dir():
            return "/dev/shm/iss_crew.db"
        else:
            # Windows fallback
            data_dir = Path.home() / ".mimic_data"
            data_dir.mkdir(exist_ok=True)
            return str(data_dir / "iss_crew.db")
    
    def load_crew_data(self):
        """Load crew data from the database."""
        try:
            db_path = self.get_db_path()
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get current crew members
            cursor.execute("""
                SELECT name, country, spaceship, expedition 
                FROM current_crew 
                ORDER BY name
            """)
            
            crew_members = cursor.fetchall()
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
                crew_widget = CrewMemberWidget(crew_data)
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
            vehicles = self.get_crewed_vehicles_on_orbit()
            total_crew = sum(v['crew_count'] for v in vehicles)
            
            # Update the crew count display
            if hasattr(self.ids, 'total_crew_count'):
                self.ids.total_crew_count.text = str(total_crew)
            
            log_info(f"Updated crewed vehicles display: {len(vehicles)} vehicles, {total_crew} total crew")
            
        except Exception as e:
            log_error(f"Error updating crewed vehicles display: {e}")
    
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
