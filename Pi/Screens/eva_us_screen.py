from __future__ import annotations
from kivy.uix.screenmanager import Screen
import pathlib
from pathlib import Path
import sqlite3
import time
import asyncio
import threading
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.network.urlrequest import UrlRequest
from ._base import MimicBase
from utils.logger import log_info, log_error

# Try to import BeautifulSoup, but make it optional
try:
    from bs4 import BeautifulSoup
    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    BEAUTIFULSOUP_AVAILABLE = False
    log_error("BeautifulSoup not available - EVA stats functionality will be limited")

kv_path = pathlib.Path(__file__).with_name("EVA_US_Screen.kv")
Builder.load_file(str(kv_path))

class EVA_US_Screen(MimicBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # EVA state tracking
        self.eva_in_progress = False
        self.standby = False
        self.prebreath1 = False
        self.depress1 = False
        self.leakhold = False
        self.depress2 = False
        self.repress = False
        
        # EVA timing
        self.eva_start_time = None
        self.hold_start_time = None
        self._eva_clock_event = None
        
        # EVA stats and astronaut management
        self.eva_stats_cache = {}
        self.current_astronauts = []
        self._eva_stats_request = None
        
        # Sustained low pressure tracking for delayed EVA triggering
        self._low_pressure_start_time = None
        self._low_pressure_samples = 0
        self._low_pressure_threshold = 2.5
        self._low_pressure_required_samples = 30  # 30 seconds at 1Hz update rate
        self._low_pressure_triggered = False
    
    def on_enter(self):
        """Start telemetry updates when screen is entered"""
        log_info("EVA US Screen: Starting telemetry updates")
        self._update_event = Clock.schedule_interval(self.update_eva_values, 1.0)
        
    def on_leave(self):
        """Stop telemetry updates when screen is left"""
        if self._update_event:
            Clock.unschedule(self._update_event)
            self._update_event = None
        if self._eva_clock_event:
            Clock.unschedule(self._eva_clock_event)
            self._eva_clock_event = None
        if self._eva_stats_request:
            self._eva_stats_request.cancel()
            self._eva_stats_request = None
        log_info("EVA US Screen: Stopped telemetry updates")
    
    def _get_db_path(self) -> Path:
        shm = Path('/dev/shm/iss_telemetry.db')
        if shm.exists():
            return shm
        return Path.home() / '.mimic_data' / 'iss_telemetry.db'
    
    def map_rotation(self, args):
        """Map pressure value to needle rotation angle"""
        scalefactor = 0.083333
        scaledValue = float(args)/scalefactor
        return scaledValue
    
    def map_psi_bar(self, args):
        """Map pressure value to PSI bar position"""
        scalefactor = 0.015
        scaledValue = (float(args)*scalefactor)+0.72
        return scaledValue
    
    def map_hold_bar(self, args):
        """Map hold timer value to hold bar position"""
        scalefactor = 0.0015
        scaledValue = (float(args)*scalefactor)+0.71
        return scaledValue
    
    def eva_clock(self, dt):
        """Update EVA clock display"""
        if not self.eva_start_time:
            return
            
        unixconvert = time.gmtime(time.time())
        currenthours = float(unixconvert[7])*24+unixconvert[3]+float(unixconvert[4])/60+float(unixconvert[5])/3600
        difference = (currenthours-self.eva_start_time)*3600
        minutes, seconds = divmod(difference, 60)
        hours, minutes = divmod(minutes, 60)
        
        hours = int(hours)
        minutes = int(minutes)
        seconds = int(seconds)
        
        self.ids.EVA_clock.text = f"{hours}:{minutes:02d}:{seconds:02d}"
        self.ids.EVA_clock.color = 0.33, 0.7, 0.18
    
    def set_current_astronauts(self, astronaut_names):
        """Set the current astronauts for EVA stats display
        
        Args:
            astronaut_names: List of tuples [(firstname, lastname), ...] or list of full names
        """
        self.current_astronauts = []
        
        for name in astronaut_names:
            if isinstance(name, tuple):
                firstname, lastname = name
            elif isinstance(name, str):
                # Try to parse full name into first and last
                parts = name.strip().split()
                if len(parts) >= 2:
                    firstname, lastname = parts[0], parts[-1]
                else:
                    firstname, lastname = name, ""
            else:
                continue
                
            self.current_astronauts.append((firstname, lastname))
        
        # Update EVA stats for current astronauts
        if self.current_astronauts:
            self.update_eva_stats_for_current_astronauts()
    
    def update_eva_stats_for_current_astronauts(self):
        """Update EVA stats display for currently assigned astronauts"""
        if not self.current_astronauts:
            return
            
        # Get stats for up to 2 astronauts
        for i, (firstname, lastname) in enumerate(self.current_astronauts[:2]):
            if i == 0:
                self.update_eva_stats_display(firstname, lastname, "EV1")
            elif i == 1:
                self.update_eva_stats_display(firstname, lastname, "EV2")
    
    def update_eva_stats_display(self, firstname, lastname, ev_position):
        """Update the display for a specific EV position with astronaut stats
        
        Args:
            firstname: Astronaut's first name
            lastname: Astronaut's last name
            ev_position: Either "EV1" or "EV2"
        """
        # Update astronaut name display
        if hasattr(self.ids, f"{ev_position}_name"):
            getattr(self.ids, f"{ev_position}_name").text = f"{firstname} {lastname}"
        
        # Check if we have cached stats
        cache_key = f"{firstname}_{lastname}".lower()
        if cache_key in self.eva_stats_cache:
            stats = self.eva_stats_cache[cache_key]
            self._display_cached_eva_stats(stats, ev_position)
        else:
            # Fetch fresh stats
            self.fetch_eva_stats(firstname, lastname, ev_position)
    
    def _display_cached_eva_stats(self, stats, ev_position):
        """Display cached EVA stats for a specific EV position"""
        if not stats:
            return
            
        num_evas = stats.get('num_evas', 0)
        total_minutes = stats.get('total_minutes', 0)
        
        hours = int(total_minutes // 60)
        minutes = int(total_minutes % 60)
        
        # Update display elements
        if hasattr(self.ids, f"{ev_position}_EVAnum"):
            getattr(self.ids, f"{ev_position}_EVAnum").text = f"Number of EVAs = {num_evas}"
        
        if hasattr(self.ids, f"{ev_position}_EVAtime"):
            getattr(self.ids, f"{ev_position}_EVAtime").text = f"Total EVA Time = {hours}h {minutes:02d}m"
    
    def fetch_eva_stats(self, firstname, lastname, ev_position):
        """Fetch EVA stats for an astronaut from spacefacts.de
        
        Args:
            firstname: Astronaut's first name
            lastname: Astronaut's last name
            ev_position: Either "EV1" or "EV2"
        """
        if not BEAUTIFULSOUP_AVAILABLE:
            log_error("BeautifulSoup not available - cannot fetch EVA stats")
            return
        
        # Cancel any existing request
        if self._eva_stats_request:
            self._eva_stats_request.cancel()
        
        eva_url = 'http://www.spacefacts.de/eva/e_eva_az.htm'
        
        def on_success(req, result):
            log_info(f"EVA stats fetch successful for {firstname} {lastname}")
            try:
                self._parse_eva_stats(result, firstname, lastname, ev_position)
            except Exception as e:
                log_error(f"Error parsing EVA stats for {firstname} {lastname}: {e}")
        
        def on_failure(req, result):
            log_error(f"EVA stats fetch failed for {firstname} {lastname}: {result}")
        
        def on_error(req, result):
            log_error(f"EVA stats fetch error for {firstname} {lastname}: {result}")
        
        # Make the request
        self._eva_stats_request = UrlRequest(
            eva_url,
            on_success=on_success,
            on_failure=on_failure,
            on_error=on_error,
            timeout=10
        )
    
    def _parse_eva_stats(self, html_content, firstname, lastname, ev_position):
        """Parse EVA stats from HTML content and update display
        
        Args:
            html_content: HTML content from spacefacts.de
            firstname: Astronaut's first name
            lastname: Astronaut's last name
            ev_position: Either "EV1" or "EV2"
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            table_tags = soup.find_all("td")
            
            num_evas = 0
            total_minutes = 0
            
            # Search for astronaut in table
            for tag in table_tags:
                if lastname.lower() in tag.text.lower():
                    # Check if first name matches in next cell
                    next_cell = tag.find_next_sibling("td")
                    if next_cell and firstname.lower() in next_cell.text.lower():
                        # Found astronaut, extract stats
                        try:
                            # Navigate to EVA count and time cells
                            eva_count_cell = next_cell.find_next_sibling("td").find_next_sibling("td").find_next_sibling("td")
                            hours_cell = eva_count_cell.find_next_sibling("td")
                            minutes_cell = hours_cell.find_next_sibling("td")
                            
                            if eva_count_cell and hours_cell and minutes_cell:
                                num_evas = eva_count_cell.text.strip()
                                hours = int(hours_cell.text.strip())
                                minutes = int(minutes_cell.text.strip())
                                total_minutes = hours * 60 + minutes
                        except (ValueError, AttributeError) as e:
                            log_error(f"Error parsing EVA stats cells for {firstname} {lastname}: {e}")
                        break
            
            # Cache the results
            cache_key = f"{firstname}_{lastname}".lower()
            self.eva_stats_cache[cache_key] = {
                'num_evas': num_evas,
                'total_minutes': total_minutes
            }
            
            # Update display
            self._display_cached_eva_stats(self.eva_stats_cache[cache_key], ev_position)
            
        except Exception as e:
            log_error(f"Error parsing EVA stats HTML: {e}")
    
    def clear_eva_stats_display(self):
        """Clear the EVA stats display"""
        for ev_position in ["EV1", "EV2"]:
            if hasattr(self.ids, f"{ev_position}_name"):
                getattr(self.ids, f"{ev_position}_name").text = ev_position
            
            if hasattr(self.ids, f"{ev_position}_EVAnum"):
                getattr(self.ids, f"{ev_position}_EVAnum").text = f"Number of EVAs = 0"
            
            if hasattr(self.ids, f"{ev_position}_EVAtime"):
                getattr(self.ids, f"{ev_position}_EVAtime").text = "Total EVA Time = 0:00"
    
    def demo_astronaut_assignment(self):
        """Demo method showing how to assign astronauts to EVA positions
        
        This method demonstrates how to use the new astronaut functionality.
        In a real implementation, you would call this when you have astronaut data
        from your telemetry or mission control systems.
        """
        # Example 1: Assign astronauts by full names
        astronauts = ["Jasmin Moghbeli", "Loral O'Hara"]
        self.set_current_astronauts(astronauts)
        
        # Example 2: Assign astronauts by first/last name tuples
        # astronauts = [("Jasmin", "Moghbeli"), ("Loral", "O'Hara")]
        # self.set_current_astronauts(astronauts)
        
        # Example 3: Assign just one astronaut
        # self.set_current_astronauts(["Jasmin Moghbeli"])
        
        log_info("Demo: Astronauts assigned to EVA positions")
    
    def get_astronaut_stats_summary(self):
        """Get a summary of current astronaut EVA stats
        
        Returns:
            dict: Summary of current astronaut EVA statistics
        """
        summary = {
            'total_astronauts': len(self.current_astronauts),
            'astronauts': []
        }
        
        for i, (firstname, lastname) in enumerate(self.current_astronauts):
            cache_key = f"{firstname}_{lastname}".lower()
            stats = self.eva_stats_cache.get(cache_key, {})
            
            astronaut_info = {
                'position': f"EV{i+1}",
                'name': f"{firstname} {lastname}",
                'num_evas': stats.get('num_evas', 0),
                'total_minutes': stats.get('total_minutes', 0),
                'cached': cache_key in self.eva_stats_cache
            }
            summary['astronauts'].append(astronaut_info)
        
        return summary
    
    def force_refresh_astronaut_stats(self):
        """Force refresh astronaut statistics by clearing cache and re-fetching"""
        if not self.current_astronauts:
            log_info("No astronauts assigned to refresh")
            return
        
        log_info("Force refreshing astronaut statistics")
        for astronaut in self.current_astronauts:
            if isinstance(astronaut, tuple):
                firstname, lastname = astronaut
            else:
                # Parse full name
                name_parts = astronaut.split()
                if len(name_parts) >= 2:
                    firstname = name_parts[0]
                    lastname = name_parts[-1]
                else:
                    continue
            
            # Clear cache for this astronaut
            cache_key = f"{firstname}_{lastname}".lower()
            if cache_key in self.eva_stats_cache:
                del self.eva_stats_cache[cache_key]
                log_info(f"Cleared cache for {firstname} {lastname}")
        
        # Re-fetch stats
        self.update_eva_stats_for_current_astronauts()
    
    def set_low_pressure_delay(self, seconds):
        """Set the delay duration for low pressure EVA triggering
        
        Args:
            seconds: Number of seconds to wait before triggering EVA in progress
        """
        if seconds < 1:
            log_error(f"Invalid delay duration: {seconds} seconds (minimum 1)")
            return
        
        self._low_pressure_required_samples = seconds
        log_info(f"Low pressure delay set to {seconds} seconds")
    
    def get_low_pressure_status(self):
        """Get current low pressure tracking status
        
        Returns:
            dict: Status information about low pressure tracking
        """
        if self._low_pressure_start_time is None:
            return {
                'tracking': False,
                'samples': 0,
                'required_samples': self._low_pressure_required_samples,
                'threshold': self._low_pressure_threshold,
                'triggered': False
            }
        
        elapsed_time = time.time() - self._low_pressure_start_time
        return {
            'tracking': True,
            'samples': self._low_pressure_samples,
            'required_samples': self._low_pressure_required_samples,
            'threshold': self._low_pressure_threshold,
            'triggered': self._low_pressure_triggered,
            'elapsed_time': elapsed_time,
            'remaining_samples': max(0, self._low_pressure_required_samples - self._low_pressure_samples)
        }
    
    def update_eva_values(self, dt):
        """Update EVA screen telemetry values"""
        try:
            # Connect to telemetry database
            db_path = self._get_db_path()
            if not db_path.exists():
                log_error(f"EVA US Screen: Database file not found at {db_path}")
                return
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute('select Value from telemetry')
            values = cur.fetchall()
            conn.close()
            
            if not values or len(values) < 73:  # Ensure we have enough data
                return
            
            # Extract EVA-related telemetry values
            crewlockpres = float(values[16][0])
            airlock_pump_voltage = int(values[71][0])
            airlock_pump_switch = int(values[72][0])
            aos_status = float(values[12][0])  # AOS status: 1.0 = connected, 0.0 = no signal, 2.0 = error
            
            # Update airlock pump status
            if airlock_pump_voltage == 1:
                self.ids.pumpvoltage.text = "Airlock Pump Power On!"
                self.ids.pumpvoltage.color = 0.33, 0.7, 0.18
            else:
                self.ids.pumpvoltage.text = "Airlock Pump Power Off"
                self.ids.pumpvoltage.color = 0, 0, 0
            
            if airlock_pump_switch == 1:
                self.ids.pumpswitch.text = "Airlock Pump Active!"
                self.ids.pumpswitch.color = 0.33, 0.7, 0.18
            else:
                self.ids.pumpswitch.text = "Airlock Pump Inactive"
                self.ids.pumpswitch.color = 0, 0, 0
            
            # EVA status logic
            airlockpres = crewlockpres  # Assuming airlock pressure is same as crewlock for now
            
            # Reset states first
            self.standby = False
            self.prebreath1 = False
            self.depress1 = False
            self.leakhold = False
            self.depress2 = False
            self.repress = False
            
            # No EVA Currently
            if airlock_pump_voltage == 0 and airlock_pump_switch == 0 and crewlockpres > 737 and airlockpres > 740:
                self.eva_in_progress = False
                self.ids.leak_timer.text = ""
                self.ids.Crewlock_Status_image.source = f"{self.mimic_directory}/Mimic/Pi/imgs/eva/BlankLights.png"
                self.ids.EVA_occuring.color = 1, 0, 0
                self.ids.EVA_occuring.text = "Currently No EVA"
                # Clear astronaut stats when no EVA
                self.clear_eva_stats_display()
                # Reset low pressure tracking when no EVA
                self._low_pressure_start_time = None
                self._low_pressure_samples = 0
                self._low_pressure_triggered = False
            
            # EVA Standby
            elif airlock_pump_voltage == 1 and airlock_pump_switch == 1 and crewlockpres > 740 and airlockpres > 740:
                self.standby = True
                self.ids.leak_timer.text = "~160s Leak Check"
                self.ids.Crewlock_Status_image.source = f"{self.mimic_directory}/Mimic/Pi/imgs/eva/StandbyLights.png"
                self.ids.EVA_occuring.color = 0, 0, 1
                self.ids.EVA_occuring.text = "EVA Standby"
                # Reset low pressure tracking when in standby
                self._low_pressure_start_time = None
                self._low_pressure_samples = 0
                self._low_pressure_triggered = False
            
            # EVA Prebreath Pressure
            elif airlock_pump_voltage == 1 and crewlockpres > 740 and airlockpres > 740:
                self.prebreath1 = True
                self.ids.Crewlock_Status_image.source = f"{self.mimic_directory}/Mimic/Pi/imgs/eva/PreBreatheLights.png"
                self.ids.leak_timer.text = "Leak Check"
                self.ids.EVA_occuring.color = 0, 0, 1
                self.ids.EVA_occuring.text = "Pre-EVA Nitrogen Purge"
                # Reset low pressure tracking when in prebreath
                self._low_pressure_start_time = None
                self._low_pressure_samples = 0
                self._low_pressure_triggered = False
            
            # EVA Depress1
            elif airlock_pump_voltage == 1 and airlock_pump_switch == 1 and crewlockpres < 740 and airlockpres > 740:
                self.depress1 = True
                self.ids.leak_timer.text = "Leak Check"
                self.ids.EVA_occuring.text = "Crewlock Depressurizing"
                self.ids.EVA_occuring.color = 0, 0, 1
                self.ids.Crewlock_Status_image.source = f"{self.mimic_directory}/Mimic/Pi/imgs/eva/DepressLights.png"
                # Reset low pressure tracking when depressurizing
                self._low_pressure_start_time = None
                self._low_pressure_samples = 0
                self._low_pressure_triggered = False
            
            # EVA Leakcheck
            elif airlock_pump_voltage == 1 and crewlockpres < 260 and crewlockpres > 250 and (self.depress1 or self.leakhold):
                if self.depress1:
                    unixconvert = time.gmtime(time.time())
                    self.hold_start_time = float(unixconvert[7])*24+float(unixconvert[3])+float(unixconvert[4])/60+float(unixconvert[5])/3600
                self.leakhold = True
                self.depress1 = False
                self.ids.EVA_occuring.text = "Leak Check in Progress!"
                self.ids.EVA_occuring.color = 0, 0, 1
                self.ids.Crewlock_Status_image.source = f"{self.mimic_directory}/Mimic/Pi/imgs/eva/LeakCheckLights.png"
                # Reset low pressure tracking when in leak check
                self._low_pressure_start_time = None
                self._low_pressure_samples = 0
                self._low_pressure_triggered = False
            
            # EVA Depress2
            elif airlock_pump_voltage == 1 and crewlockpres <= 250 and crewlockpres > 3:
                self.leakhold = False
                self.ids.leak_timer.text = "Complete"
                self.ids.EVA_occuring.text = "Crewlock Depressurizing"
                self.ids.EVA_occuring.color = 0, 0, 1
                self.ids.Crewlock_Status_image.source = f"{self.mimic_directory}/Mimic/Pi/imgs/eva/DepressLights.png"
                # Reset low pressure tracking when depressurizing
                self._low_pressure_start_time = None
                self._low_pressure_samples = 0
                self._low_pressure_triggered = False
            
            # EVA in progress - with delayed triggering and AOS status check
            elif crewlockpres < self._low_pressure_threshold:
                # Check if we have AOS (telemetry acquired)
                if aos_status == 1.0:  # AOS active
                    # Start or continue tracking sustained low pressure
                    if self._low_pressure_start_time is None:
                        self._low_pressure_start_time = time.time()
                        self._low_pressure_samples = 0
                    
                    self._low_pressure_samples += 1
                    
                    # Check if we've had sustained low pressure for required duration
                    if (self._low_pressure_samples >= self._low_pressure_required_samples and 
                        not self._low_pressure_triggered):
                        
                        self._low_pressure_triggered = True
                        self.eva_in_progress = True
                        self.ids.EVA_occuring.text = "EVA In Progress!!!"
                        self.ids.EVA_occuring.color = 0.33, 0.7, 0.18
                        self.ids.leak_timer.text = "Complete"
                        self.ids.Crewlock_Status_image.source = f"{self.mimic_directory}/Mimic/Pi/imgs/eva/InProgressLights.png"
                        
                        # Start EVA clock if not already running
                        if not self._eva_clock_event:
                            unixconvert = time.gmtime(time.time())
                            self.eva_start_time = float(unixconvert[7])*24+float(unixconvert[3])+float(unixconvert[4])/60+float(unixconvert[5])/3600
                            self._eva_clock_event = Clock.schedule_interval(self.eva_clock, 1.0)
                        
                        log_info(f"EVA In Progress triggered after {self._low_pressure_samples} samples of sustained low pressure ({self._low_pressure_threshold} PSI) with AOS active")
                    else:
                        # Still tracking, show intermediate status
                        remaining_samples = self._low_pressure_required_samples - self._low_pressure_samples
                        self.ids.EVA_occuring.text = f"Pressure Low - {remaining_samples}s to EVA"
                        self.ids.EVA_occuring.color = 1, 1, 0  # Yellow
                        self.ids.leak_timer.text = f"~{remaining_samples}s"
                        self.ids.Crewlock_Status_image.source = f"{self.mimic_directory}/Mimic/Pi/imgs/eva/DepressLights.png"
                else:
                    # No AOS, reset tracking and show waiting status
                    self._low_pressure_start_time = None
                    self._low_pressure_samples = 0
                    self._low_pressure_triggered = False
                    self.ids.EVA_occuring.text = "Waiting for Telemetry"
                    self.ids.EVA_occuring.color = 1, 1, 0  # Yellow
                    self.ids.leak_timer.text = "No AOS"
                    self.ids.Crewlock_Status_image.source = f"{self.mimic_directory}/Mimic/Pi/imgs/eva/BlankLights.png"
            
            # Repress
            elif airlock_pump_voltage == 1 and airlock_pump_switch == 1 and crewlockpres >= 3 and crewlockpres < 734:
                self.eva_in_progress = False
                self.ids.EVA_occuring.color = 0, 0, 1
                self.ids.EVA_occuring.text = "Crewlock Repressurizing"
                self.ids.Crewlock_Status_image.source = f"{self.mimic_directory}/Mimic/Pi/imgs/eva/RepressLights.png"
                # Reset low pressure tracking when repressurizing
                self._low_pressure_start_time = None
                self._low_pressure_samples = 0
                self._low_pressure_triggered = False
            
            # Update pressure needle and bar
            psi_value = 0.0193368 * float(crewlockpres)
            self.ids.EVA_needle.angle = float(self.map_rotation(psi_value))
            self.ids.crewlockpressure_value.text = "{:.2f}".format(psi_value)
            
            psi_bar_x = self.map_psi_bar(psi_value)
            self.ids.EVA_psi_bar.pos_hint = {"center_x": psi_bar_x, "center_y": 0.61}
            
        except Exception as e:
            log_error(f"EVA US Screen update failed: {e}")
            if 'conn' in locals():
                conn.close()
