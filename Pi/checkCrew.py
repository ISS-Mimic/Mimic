#!/usr/bin/env python3
"""
Fetch current ISS crew from Wikipedia and store in SQLite.

- Runs once and exits (subprocess-friendly).
- Creates schema on first run.
- Saves a historical snapshot only when data changes (by checksum).
- Keeps a "current" table always reflecting the latest snapshot.

Usage:
    python checkCrew.py

Exit codes:
    0 = success, regardless of change
    1 = unrecoverable error
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import requests
from bs4 import BeautifulSoup

from utils.logger import log_info, log_error

WIKI_API_URL = (
    "https://en.wikipedia.org/w/api.php"
    "?action=parse&page=Template:People_currently_in_space&prop=wikitext&format=json"
)

def get_db_path() -> str:
    """Get the database path, prioritizing /dev/shm on Linux."""
    if Path("/dev/shm").exists() and Path("/dev/shm").is_dir():
        return "/dev/shm/iss_crew.db"
    else:
        # Windows fallback
        data_dir = Path.home() / ".mimic_data"
        data_dir.mkdir(exist_ok=True)
        return str(data_dir / "iss_crew.db")

# --- Network / scraping ----------------------------------------------------- #

def fetch_spacefacts_crew(max_attempts: int = 3, timeout: int = 10) -> List[Dict[str, str]]:
    """
    Fetch detailed crew data from Spacefacts.de ISS table.
    Returns list of dicts with enhanced crew information.
    """
    # Get the latest expedition number once at the beginning
    expedition_number = get_latest_expedition_number()
    log_info(f"Found expedition number: {expedition_number}")
    
    # Get the latest expedition URL dynamically
    current_url = get_spacefacts_url(expedition_number)
    log_info(f"Fetching crew data from: {current_url}")
    
    headers = {
        "User-Agent": "ISS-Mimic Bot (+https://github.com/ISS-Mimic; iss.mimic@gmail.com)"
    }

    last_exc = None
    for attempt in range(max_attempts):
        try:
            log_info(f"Attempting to fetch Spacefacts.de crew data (attempt {attempt + 1}/{max_attempts})")
            r = requests.get(current_url, headers=headers, timeout=timeout)
            r.raise_for_status()
            
            # Parse the HTML table
            soup = BeautifulSoup(r.content, 'html.parser')
            
            # Find the ISS crew table - look for the crew data table
            tables = soup.find_all('table')

            crew_table = None
            # Look for the crew table with the specific structure
            for table in tables:
                table_text = str(table)
                headers = ['No.', 'Nation', 'Surname', 'Given names', 'Position']
                if all(any(h in cell.get_text() for cell in table.find_all(['td', 'th'])) for h in headers):
                    crew_table = table
                    break
            
            if not crew_table:
                log_error("No ISS crew table found on Spacefacts.de")
                return []
            
            crew_info = []
            rows = crew_table.find_all('tr')[1:]  # Skip header row

            # Collect all astronaut URLs first, then fetch them all
            astronaut_urls = []
            for row_index, row in enumerate(rows):
                cells = row.find_all(['td', 'th'])
                # Skip rows that don't have enough data or are header rows
                if len(cells) < 12:  # Need at least 12 columns for complete crew data
                    continue
                
                # Check if this row contains crew data (should have a number in first cell)
                first_cell = cells[0].get_text(strip=True)
                # Look for crew number pattern (1, 2, 3, etc.)
                if not first_cell.isdigit():
                    continue

                
                try:
                    # Extract country from flag image
                    country_cell = cells[1]
                    country = "Unknown"
                    if country_cell.find('img'):
                        img = country_cell.find('img')
                        country = img.get('title', img.get('alt', 'Unknown'))
                        if country == 'Unknown':
                            # Try to extract from the image filename
                            src = img.get('src', '')
                            if 'usa.gif' in src:
                                country = 'USA'
                            elif 'russia.gif' in src:
                                country = 'Russia'
                            elif 'japan.gif' in src:
                                country = 'Japan'
                            elif 'canada.gif' in src:
                                country = 'Canada'
                            elif 'china.gif' in src:
                                country = 'China'
                            elif 'gb.gif' in src:
                                country = 'United Kingdom'
                            elif 'italy.gif' in src:
                                country = 'Italy'
                            elif 'france.gif' in src:
                                country = 'France'
                            elif 'germany.gif' in src:
                                country = 'Germany'
                            elif 'netherlands.gif' in src:
                                country = 'Netherlands'
                            elif 'sweden.gif' in src:
                                country = 'Sweden'
                            elif 'norway.gif' in src:
                                country = 'Norway'
                            elif 'denmark.gif' in src:
                                country = 'Denmark'
                            elif 'poland.gif' in src:
                                country = 'Poland'
                            elif 'belgium.gif' in src:
                                country = 'Belgium'
                            elif 'spain.gif' in src:
                                country = 'Spain'

                    if country == 'Russian Federation':
                        country = 'Russia'
                    
                    # Parse the table row based on the Expedition 73 table structure
                    # Extract name with preference for nicknames in quotes
                    given_names = cells[3].get_text(strip=True)
                    surname = cells[2].get_text(strip=True)
                    
                    # Check for nickname in quotes (e.g., "Annimal", "Vapor", "Jonny")
                    nickname_match = re.search(r'"([^"]+)"', given_names)
                    if nickname_match:
                        # Use the nickname instead of first name
                        first_name = nickname_match.group(1)
                    else:
                        # Use the first word of given names
                        first_name = given_names.split()[0]
                    
                    # Extract astronaut image URL from surname link
                    image_url = None
                    surname_cell = cells[2]
                    if surname_cell.find('a'):
                        link = surname_cell.find('a')
                        href = link.get('href', '')
                        if href:
                            # Convert relative URL to absolute URL using the actual href from the table
                            if href.startswith('..'):
                                # Handle relative paths like "../../bios/international/english/onishi_takuya.htm"
                                # Convert to absolute URL by going up the path and then down to the bios directory
                                path_parts = href.split('/')
                                # Remove the ".." parts and construct the full URL
                                if len(path_parts) >= 4:  # Should have at least ../../bios/category/language/filename
                                    category = path_parts[3]  # e.g., "international", "cosmonauts", "astronauts"
                                    language = path_parts[4]  # e.g., "english"
                                    filename = path_parts[5]  # e.g., "onishi_takuya.htm"
                                    astronaut_page_url = f"https://spacefacts.de/bios/{category}/{language}/{filename}"
                                else:
                                    astronaut_page_url = None
                            elif href.startswith('/'):
                                # Handle absolute paths
                                astronaut_page_url = f"https://spacefacts.de{href}"
                            elif href.startswith('http'):
                                # Already absolute URL
                                astronaut_page_url = href
                            else:
                                astronaut_page_url = None
                            
                            # Now fetch the actual image URL from the astronaut's page
                            if astronaut_page_url:
                                image_url = get_astronaut_image_url(astronaut_page_url)
                                
                                # Also fetch mission data for total time in space calculation
                                mission_data = get_astronaut_mission_data(astronaut_page_url)
                            else:
                                image_url = None
                                mission_data = {'total_time_in_space': 0, 'current_mission_duration': 0}
                    
                    crew_member = {
                        'name': f"{first_name} {surname}",  # Nickname (if available) + Surname
                        'country': country,  # Nation extracted from flag image
                        'position': cells[4].get_text(strip=True),  # Position
                        'spaceship': cells[5].get_text(strip=True),  # Spacecraft (launch)
                        'launch_date': cells[6].get_text(strip=True),  # Launch date
                        'launch_time': cells[7].get_text(strip=True),  # Launch time
                        'landing_spacecraft': cells[8].get_text(strip=True),  # Spacecraft (landing)
                        'landing_date': cells[9].get_text(strip=True),  # Landing date
                        'landing_time': cells[10].get_text(strip=True),  # Landing time
                        'mission_duration': '',  # Will be calculated by crew screen based on launch time
                        #'orbits': cells[12].get_text(strip=True),  # Orbits - removed from webpage
                        'orbits': None,
                        'expedition': f"Expedition {expedition_number}",  # Use expedition number found at start
                        'image_url': image_url,  # URL to astronaut's personal page with image
                        'total_time_in_space': mission_data['total_time_in_space'],  # Total lifetime days in space
                        'current_mission_duration': mission_data['current_mission_duration']  # Current mission duration in days
                    }

                    # Clean up the data
                    crew_member['name'] = crew_member['name'].strip()
                    crew_member['country'] = crew_member['country'].strip()
                    crew_member['position'] = crew_member['position'].strip()
                    
                    # Parse launch date (DD.MM.YYYY format)
                    if crew_member['launch_date'] and crew_member['launch_date'] != '':
                        try:
                            day, month, year = crew_member['launch_date'].split('.')
                            crew_member['launch_date'] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                        except:
                            crew_member['launch_date'] = None
                    else:
                        crew_member['launch_date'] = None
                    
                    # Parse landing date
                    if crew_member['landing_date'] and crew_member['landing_date'] not in ['', '(??.01.2026)', '(09.12.2025)']:
                        try:
                            if crew_member['landing_date'].startswith('(') and crew_member['landing_date'].endswith(')'):
                                # Future landing date, extract the date part
                                date_part = crew_member['landing_date'][1:-1]
                                if '.' in date_part:
                                    day, month, year = date_part.split('.')
                                    crew_member['landing_date'] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                                    crew_member['status'] = 'active'
                                else:
                                    crew_member['landing_date'] = None
                                    crew_member['status'] = 'active'
                            else:
                                # Past landing date
                                day, month, year = crew_member['landing_date'].split('.')
                                crew_member['landing_date'] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                                crew_member['status'] = 'returned'
                        except:
                            crew_member['landing_date'] = None
                            crew_member['status'] = 'active'
                    else:
                        crew_member['landing_date'] = None
                        crew_member['status'] = 'active'
                    
                    # Parse orbits (remove any non-numeric characters)
                    try:
                        orbits_text = crew_member['orbits'].strip()
                        if orbits_text and orbits_text != '':
                            orbits_num = int(''.join(filter(str.isdigit, orbits_text)))
                            crew_member['orbits'] = orbits_num
                        else:
                            crew_member['orbits'] = None
                    except:
                        crew_member['orbits'] = None
                    
                    # Only include crew members who have actually launched (have a launch date and specific launch time)
                    # AND are currently active (not returned)
                    if (crew_member['launch_date'] and crew_member['launch_date'].strip() and 
                        crew_member['launch_time'] and crew_member['launch_time'].strip() != 'UTC' and
                        crew_member['status'] == 'active'):
                        crew_info.append(crew_member)
                    else:
                        # Skip crew members who haven't launched or have returned
                        pass
                        
                except Exception as e:
                    log_error(f"Error parsing crew member row: {e}")
                    continue
            
            log_info(f"Successfully fetched {len(crew_info)} crew members from Spacefacts.de")
            return crew_info
            
        except requests.RequestException as exc:
            last_exc = exc
            log_error(f"Request failed on attempt {attempt + 1}: {exc}")
        except Exception as exc:
            last_exc = exc
            log_error(f"Unexpected error on attempt {attempt + 1}: {exc}")

    # If we get here, all attempts failed
    error_msg = f"Failed to fetch Spacefacts.de crew data after {max_attempts} attempts: {last_exc}"
    log_error(error_msg)
    return []  # Return empty list instead of raising, so Wikipedia fallback can work

def fetch_iss_crew(max_attempts: int = 3, timeout: int = 10) -> List[Dict[str, str]]:
    """
    Returns list of dicts: [{name, spaceship, country, expedition}, ...]
    """
    headers = {
        "User-Agent": "ISS-Mimic/1.0 (+https://example.local; admin@localhost)"
    }

    last_exc = None
    for attempt in range(max_attempts):
        try:
            log_info(f"Attempting to fetch ISS crew data (attempt {attempt + 1}/{max_attempts})")
            r = requests.get(WIKI_API_URL, headers=headers, timeout=timeout)
            r.raise_for_status()
            data = r.json()
            template_content = data["parse"]["wikitext"]["*"]

            # Isolate ISS section up to Tiangong (section order can vary occasionally)
            iss_match = re.search(
                r"International Space Station.*?(?=Tiangong space station|$)",
                template_content,
                re.DOTALL,
            )
            if not iss_match:
                log_info("No ISS section found in Wikipedia template")
                return []

            iss_section = iss_match.group(0)

            # Extract wikilinks and tiny flag "country" labels
            # Example link tokens often look like [[Sergey Prokopyev (cosmonaut)|Sergey Prokopyev]]
            links = re.findall(r"\[\[([^\]]+)\]\]", iss_section)
            countries = re.findall(r"size=15px\|([^}\n]+)", iss_section)

            crew_info: List[Dict[str, str]] = []
            current_ship = ""
            expedition = ""
            country_idx = 0

            def clean_link_token(tok: str) -> str:
                # Use the display text if present; otherwise the link target
                # e.g. "Name (astronaut)|Name" -> "Name"
                parts = tok.split("|")
                text = parts[-1].strip()
                return re.sub(r"\s+", " ", text)

            for token in links:
                text = clean_link_token(token)

                if "Expedition" in text:
                    expedition = text
                    continue

                if any(key in text for key in ("SpaceX", "Soyuz", "Axiom", "Boeing")):
                    current_ship = text
                    continue

                # Otherwise: astronaut name
                country = countries[country_idx].strip() if country_idx < len(countries) else "Unknown"
                country_idx += 1
                crew_info.append(
                    {
                        "name": text,
                        "spaceship": current_ship or "Unknown",
                        "country": country,
                        "expedition": expedition or "Unknown",
                    }
                )

            log_info(f"Successfully fetched {len(crew_info)} crew members")
            return crew_info

        except requests.RequestException as exc:
            last_exc = exc
            log_error(f"Request failed on attempt {attempt + 1}: {exc}")

    # If we get here, all attempts failed
    error_msg = f"Failed to fetch ISS crew after {max_attempts} attempts: {last_exc}"
    log_error(error_msg)
    raise RuntimeError(error_msg)

def get_latest_expedition_number() -> int:
    """
    Discover the latest ISS expedition number by checking Spacefacts.de.
    Returns the expedition number as an integer.
    """
    base_url = "https://spacefacts.de/iss/english/"
    headers = {
        "User-Agent": "ISS-Mimic/1.0 (+https://github.com/ISS-Mimic; iss.mimic@gmail.com)"
    }
    
    # Start from a known good number and work up/down more efficiently
    # We know Expedition 73 exists, so start there
    for exp_num in range(73, 85):  # Try expeditions 73 up to 84
        test_url = f"{base_url}exp_{exp_num}.htm"
        try:
            r = requests.get(test_url, headers=headers, timeout=5)
            if r.status_code == 200:
                # Quick check - just look for expedition number in text
                if f"expedition {exp_num}" in r.text.lower():
                    return exp_num
        except Exception:
            continue
    
    # If we can't find any working expeditions above 73, try a few below
    for exp_num in range(72, 69, -1):  # Try expeditions 72 down to 69
        test_url = f"{base_url}exp_{exp_num}.htm"
        try:
            r = requests.get(test_url, headers=headers, timeout=5)
            if r.status_code == 200:
                if f"expedition {exp_num}" in r.text.lower():
                    return exp_num
        except Exception:
            continue
    
    # If all else fails, return a reasonable default
    log_info("Could not determine expedition number, using default: 73")
    return 73

def get_spacefacts_url(expedition_num: int = None) -> str:
    """
    Get the Spacefacts.de URL for the specified expedition.
    If no expedition number is provided, discover the latest one.
    """
    if expedition_num is None:
        expedition_num = get_latest_expedition_number()
    return f"https://spacefacts.de/iss/english/exp_{expedition_num}.htm"

def get_astronaut_image_url(astronaut_page_url: str) -> str:
    """
    Extract the astronaut's image URL from their personal page.
    Returns the direct image URL or None if not found.
    """
    if not astronaut_page_url:
        return None
    
    headers = {
        "User-Agent": "ISS-Mimic Bot (+https://github.com/ISS-Mimic; iss.mimic@gmail.com)"
    }
    
    try:
        r = requests.get(astronaut_page_url, headers=headers, timeout=10)
        r.raise_for_status()
        
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # First, look for the high-resolution portrait link that's often in the page
        # Based on the example page, it's often a link to "hi res version"
        portrait_links = soup.find_all('a', href=re.compile(r'portraits.*\.jpg'))
        if portrait_links:
            for link in portrait_links:
                href = link.get('href', '')
                if 'portraits' in href and href.endswith('.jpg'):
                    if href.startswith('..'):
                        # Convert relative path to absolute
                        # Extract the category from the astronaut page URL to use the correct path
                        if 'bios/' in astronaut_page_url:
                            category = astronaut_page_url.split('bios/')[1].split('/')[0]
                            # Handle different portrait directories based on category
                            if category == 'cosmonauts':
                                return f"https://spacefacts.de/bios/portraits_hi/cosmonauts/{href.split('/')[-1]}"
                            elif category == 'astronauts':
                                return f"https://spacefacts.de/bios/portraits2/astronauts/{href.split('/')[-1]}"
                            else:
                                # Default to portraits_hi for other categories
                                return f"https://spacefacts.de/bios/portraits_hi/{category}/{href.split('/')[-1]}"
                        else:
                            # Fallback if we can't determine category
                            return f"https://spacefacts.de/bios/portraits_hi/international/{href.split('/')[-1]}"
                    elif href.startswith('/'):
                        return f"https://spacefacts.de{href}"
                    elif href.startswith('http'):
                        return href
                    else:
                        # Assume it's relative to the current page
                        base_url = '/'.join(astronaut_page_url.split('/')[:-1])
                        return f"{base_url}/{href}"
        
        # Look for the astronaut's photo - typically in a table or specific div
        # Common patterns: look for images with astronaut names or in specific table cells
        images = soup.find_all('img')
        
        for img in images:
            src = img.get('src', '')
            alt = img.get('alt', '').lower()
            title = img.get('title', '').lower()
            
            # Look for images that are likely astronaut photos
            if any(keyword in alt or keyword in title for keyword in ['astronaut', 'cosmonaut', 'photo', 'portrait']):
                if src.startswith('..'):
                    # Convert relative path to absolute
                    # Extract the category from the astronaut page URL to use the correct path
                    if 'bios/' in astronaut_page_url:
                        category = astronaut_page_url.split('bios/')[1].split('/')[0]
                        return f"https://spacefacts.de/bios/{category}/english/{src.split('/')[-1]}"
                    else:
                        return f"https://spacefacts.de/bios/international/english/{src.split('/')[-1]}"
                elif src.startswith('/'):
                    return f"https://spacefacts.de{src}"
                elif src.startswith('http'):
                    return src
                else:
                    # Assume it's relative to the current page
                    base_url = '/'.join(astronaut_page_url.split('/')[:-1])
                    return f"{base_url}/{src}"
        
        # Fallback: look for any image that might be the astronaut photo
        # Often the first image after the name/title
        for img in images:
            src = img.get('src', '')
            if src and not src.endswith('.gif') and 'flag' not in src.lower():
                if src.startswith('..'):
                    # Extract the category from the astronaut page URL to use the correct path
                    if 'bios/' in astronaut_page_url:
                        category = astronaut_page_url.split('bios/')[1].split('/')[0]
                        return f"https://spacefacts.de/bios/{category}/english/{src.split('/')[-1]}"
                    else:
                        return f"https://spacefacts.de/bios/international/english/{src.split('/')[-1]}"
                elif src.startswith('/'):
                    return f"https://spacefacts.de{src}"
                elif src.startswith('http'):
                    return src
                else:
                    base_url = '/'.join(astronaut_page_url.split('/')[:-1])
                    return f"{base_url}/{src}"
        
        return None
        
    except Exception as e:
        log_error(f"Error fetching astronaut image from {astronaut_page_url}: {e}")
        return None

def get_astronaut_mission_data(astronaut_page_url: str) -> dict:
    """
    Extract mission data from the astronaut's Spaceflights table.
    Returns dict with total_time_in_space and current_mission_duration.
    """
    if not astronaut_page_url:
        return {'total_time_in_space': 0, 'current_mission_duration': 0}
    
    headers = {
        "User-Agent": "ISS-Mimic Bot (+https://github.com/ISS-Mimic; iss.mimic@gmail.com)"
    }
    
    try:
        r = requests.get(astronaut_page_url, headers=headers, timeout=10)
        r.raise_for_status()
        
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # Look for the Spaceflights table
        spaceflights_header = soup.find('h3', string='Spaceflights')
        if not spaceflights_header:
            return {'total_time_in_space': 0, 'current_mission_duration': 0}
        
        # Find the table after the Spaceflights header
        table = spaceflights_header.find_next('table')
        if not table:
            return {'total_time_in_space': 0, 'current_mission_duration': 0}
        
        total_time = 0
        current_mission_days = 0
        today = datetime.now()
        
        # Parse each row in the table
        rows = table.find_all('tr')[1:]  # Skip header row
        for row in rows:
            cells = row.find_all('td')
            if len(cells) < 5:
                continue
            
            # Check if this is a summary row (Total)
            if 'Total' in str(cells[0]):
                continue
            
            # Check if this row has mission data
            mission_cell = cells[1].get_text(strip=True)
            if not mission_cell or mission_cell.isspace():
                continue
            
            # Get the time column (4th column, index 3)
            time_cell = cells[3].get_text(strip=True)
            if not time_cell or time_cell.isspace():
                continue
            
            # Parse the time range
            if ' - ' in time_cell:
                # Completed mission: "19.10.2016 - 10.04.2017"
                try:
                    start_date_str, end_date_str = time_cell.split(' - ')
                    start_date = datetime.strptime(start_date_str.strip(), '%d.%m.%Y')
                    end_date = datetime.strptime(end_date_str.strip(), '%d.%m.%Y')
                    mission_duration = (end_date - start_date).days
                    total_time += mission_duration
                except ValueError:
                    continue
            else:
                # Current mission: "08.04.2025" (single date)
                try:
                    launch_date = datetime.strptime(time_cell.strip(), '%d.%m.%Y')
                    current_mission_days = (today - launch_date).days
                    total_time += current_mission_days
                except ValueError:
                    continue
        
        return {
            'total_time_in_space': total_time,
            'current_mission_duration': current_mission_days
        }
        
    except Exception as e:
        log_error(f"Error fetching astronaut mission data from {astronaut_page_url}: {e}")
        return {'total_time_in_space': 0, 'current_mission_duration': 0}

def format_duration_days(days: int) -> str:
    """
    Format duration in days to human-readable format (e.g., "2 years, 3 months, 15 days").
    """
    if days < 1:
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

# --- Persistence ------------------------------------------------------------ #

def ensure_schema(conn: sqlite3.Connection) -> None:
    """Ensure the database schema exists."""
    try:
        #log_info("Creating/updating crew database schema")
        
        # Force recreation of tables to ensure correct schema
        #log_info("Recreating database tables to ensure correct schema")
        conn.executescript("""
            DROP TABLE IF EXISTS crew_members;
            DROP TABLE IF EXISTS current_crew;
            DROP TABLE IF EXISTS snapshots;
        """)
        
        # Create tables explicitly without IF NOT EXISTS
        conn.executescript("""
            PRAGMA journal_mode=WAL;
            PRAGMA synchronous=NORMAL;

            CREATE TABLE snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fetched_at TEXT NOT NULL,          -- ISO 8601 UTC
                checksum TEXT NOT NULL UNIQUE      -- checksum of normalized payload
            );

            CREATE TABLE crew_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                country TEXT NOT NULL,
                spaceship TEXT NOT NULL,
                expedition TEXT NOT NULL,
                position TEXT,                    -- ISS-CDR, Flight Engineer, etc.
                launch_date TEXT,                 -- Launch date (YYYY-MM-DD)
                launch_time TEXT,                 -- Launch time (HH:MM:SS UTC)
                landing_spacecraft TEXT,          -- Spacecraft (landing) or NULL if active
                landing_date TEXT,                -- Landing date (YYYY-MM-DD) or NULL if active
                landing_time TEXT,                -- Landing time (HH:MM:SS UTC) or NULL if active
                mission_duration TEXT,            -- Mission duration (e.g., "147d 16h 29m 52s")
                orbits INTEGER,                   -- Number of orbits completed
                status TEXT DEFAULT 'active',     -- 'active' or 'returned'
                image_url TEXT,                   -- URL to astronaut's photo
                total_time_in_space INTEGER,      -- Total lifetime days in space
                current_mission_duration INTEGER  -- Current mission duration in days
            );

            CREATE TABLE current_crew (
                name TEXT NOT NULL,
                country TEXT NOT NULL,
                spaceship TEXT NOT NULL,
                expedition TEXT NOT NULL,
                position TEXT,
                launch_date TEXT,
                launch_time TEXT,
                landing_spacecraft TEXT,
                landing_date TEXT,
                landing_time TEXT,
                mission_duration TEXT,
                orbits INTEGER,
                status TEXT DEFAULT 'active',
                image_url TEXT,                   -- URL to astronaut's photo
                total_time_in_space INTEGER,      -- Total lifetime days in space
                current_mission_duration INTEGER  -- Current mission duration in days
            );
        """)
        conn.commit()
        #log_info("Database schema recreated successfully")
        
        # Verify the schema was created correctly
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(crew_members)")
        columns = cursor.fetchall()
        #log_info(f"crew_members table has {len(columns)} columns:")
        #for col in columns:
        #    log_info(f"  {col[1]} ({col[2]})")
        
    except sqlite3.Error as e:
        log_error(f"Failed to create database schema: {e}")
        raise

def normalize_for_checksum(crew: List[Dict[str, str]]) -> str:
    """
    Build a stable string for checksumming (order-independent).
    """
    normalized = sorted(
        [{k: v.strip() if isinstance(v, str) else v for k, v in member.items()} for member in crew],
        key=lambda m: (m["name"], m["spaceship"], m["country"], m["expedition"]),
    )
    return json.dumps(normalized, ensure_ascii=False, separators=(",", ":"))

def compute_checksum(crew: List[Dict[str, str]]) -> str:
    norm = normalize_for_checksum(crew)
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()

def get_last_checksum(conn: sqlite3.Connection) -> str | None:
    try:
        row = conn.execute("SELECT checksum FROM snapshots ORDER BY id DESC LIMIT 1").fetchone()
        return row[0] if row else None
    except sqlite3.Error as e:
        log_error(f"Failed to get last checksum: {e}")
        return None

def insert_snapshot(conn: sqlite3.Connection, crew: List[Dict[str, str]], checksum: str) -> int:
    """Insert a new crew snapshot into the database."""
    try:
        fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        cur = conn.cursor()
        
        #log_info(f"Inserting new crew snapshot with {len(crew)} members")
        cur.execute("INSERT INTO snapshots (fetched_at, checksum) VALUES (?, ?)", (fetched_at, checksum))
        snapshot_id = cur.lastrowid

        cur.executemany(
            """
            INSERT INTO crew_members (snapshot_id, name, country, spaceship, expedition, position, launch_date, launch_time, landing_spacecraft, landing_date, landing_time, mission_duration, orbits, status, image_url, total_time_in_space, current_mission_duration)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (snapshot_id, m["name"], m["country"], m["spaceship"], m["expedition"], 
                 m.get("position"), m.get("launch_date"), m.get("launch_time"), 
                 m.get("landing_spacecraft"), m.get("landing_date"), m.get("landing_time"), m.get("mission_duration"), 
                 m.get("orbits"), m.get("status", "active"), m.get("image_url"), 
                 m.get("total_time_in_space", 0), m.get("current_mission_duration", 0))
                for m in crew
            ],
        )

        # Refresh current_crew to mirror this snapshot
        cur.execute("DELETE FROM current_crew")
        cur.executemany(
            """
            INSERT INTO current_crew (name, country, spaceship, expedition, position, launch_date, launch_time, 
                landing_spacecraft, landing_date, landing_time, mission_duration, orbits, status, image_url, total_time_in_space, current_mission_duration) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [(m["name"], m["country"], m["spaceship"], m["expedition"], 
            m.get("position"), m.get("launch_date"), m.get("launch_time"), 
            m.get("landing_spacecraft"), m.get("landing_date"), m.get("landing_time"),
            m.get("mission_duration"), m.get("orbits"), m.get("status", "active"), m.get("image_url"),
            m.get("total_time_in_space", 0), m.get("current_mission_duration", 0)) for m in crew],
        )


        conn.commit()
        log_info(f"Successfully inserted snapshot {snapshot_id}")
        return snapshot_id
        
    except sqlite3.Error as e:
        log_error(f"Failed to insert crew snapshot: {e}")
        raise

def main() -> int:
    try:
        db_path = get_db_path()
        log_info(f"Using database: {db_path}")
        
        # Check if database directory exists
        db_file = Path(db_path)
        db_dir = db_file.parent
        #log_info(f"Database directory: {db_dir}")
        #log_info(f"Database directory exists: {db_dir.exists()}")
        
        # Add timeout to database connection
        conn = sqlite3.connect(db_path, timeout=30.0)
        conn.isolation_level = None  # Enable autocommit mode
        
        #log_info("Database connection successful")
        ensure_schema(conn)

        log_info("Fetching current ISS crew data from Spacefacts.de")
        crew = fetch_spacefacts_crew()
        
        # If Spacefacts.de fails, fall back to Wikipedia
        if not crew:
            log_info("Spacefacts.de fetch failed, falling back to Wikipedia")
            crew = fetch_iss_crew()
        
        # If fetch returns empty (unexpected), we still write a snapshot so the
        # main app can notice the empty state if it changed.
        checksum = compute_checksum(crew)
        log_info(f"Computed checksum: {checksum[:8]}...")

        last = get_last_checksum(conn)
        if last == checksum:
            log_info("No changes detected in crew data")
            return 0

        log_info("Crew data has changed, inserting new snapshot")
        insert_snapshot(conn, crew, checksum)
        log_info("Crew data update completed successfully")
        return 0

    except Exception as e:
        log_error(f"Unrecoverable error in checkCrew: {e}")
        return 1

    finally:
        try:
            if 'conn' in locals():
                conn.close()
                log_info("Database connection closed")
        except Exception as e:
            log_error(f"Error closing database connection: {e}")


if __name__ == "__main__":
    # Add a simple test mode
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        try:
            db_path = get_db_path()
            conn = sqlite3.connect(db_path, timeout=10.0)
            conn.isolation_level = None
            
            ensure_schema(conn)
            
            # Test with dummy data
            test_crew = [{
                'name': 'Test Astronaut',
                'country': 'Test Country',
                'spaceship': 'Test Ship',
                'expedition': 'Test Expedition',
                'position': 'Test Position',
                'launch_date': '2025-01-01',
                'launch_time': '12:00:00',
                'landing_date': None,
                'landing_time': None,
                'mission_duration': '1d',
                'orbits': 1,
                'status': 'active',
                'image_url': 'https://example.com/test.jpg',
                'total_time_in_space': 365,
                'current_mission_duration': 30
            }]
            
            checksum = compute_checksum(test_crew)
            insert_snapshot(conn, test_crew, checksum)
            conn.close()
            sys.exit(0)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        sys.exit(main())
