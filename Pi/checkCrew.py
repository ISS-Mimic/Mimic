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

SPACEFACTS_URL = "https://spacefacts.de/iss/english/exp_73.htm"

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
    print("Fetching Spacefacts.de crew data")
    """
    Fetch detailed crew data from Spacefacts.de ISS table.
    Returns list of dicts with enhanced crew information.
    """
    headers = {
        "User-Agent": "ISS-Mimic/1.0 (+https://github.com/ISS-Mimic; iss.mimic@gmail.com)"
    }

    last_exc = None
    for attempt in range(max_attempts):
        try:
            log_info(f"Attempting to fetch Spacefacts.de crew data (attempt {attempt + 1}/{max_attempts})")
            r = requests.get(SPACEFACTS_URL, headers=headers, timeout=timeout)
            r.raise_for_status()
            
            # Parse the HTML table
            soup = BeautifulSoup(r.content, 'html.parser')
            
            # Find the ISS crew table - look for the crew data table
            tables = soup.find_all('table')

            print(f"Found {len(tables)} tables")

            crew_table = None
            # Look for the crew data table with the specific structure
            for i, table in enumerate(tables):
                table_text = str(table)
                print(f"Table {i}: {table_text[:200]}...")  # Show first 200 chars of each table
                
                # Look for the crew table with the specific headers
                if ('No.' in table_text and 'Nation' in table_text and 'Surname' in table_text and 
                    'Given names' in table_text and 'Position' in table_text):
                    crew_table = table
                    print(f"Found crew table at index {i}")
                    break
            
            if not crew_table:
                log_info("No ISS crew table found on Spacefacts.de")
                print(f"No ISS crew table found on Spacefacts.de")

                return []
            
            print(f"Found crew table with {len(crew_table.find_all('tr'))} rows")
            
            # Debug: Show the header row to understand the structure
            header_row = crew_table.find_all('tr')[0] if crew_table.find_all('tr') else None
            if header_row:
                header_cells = header_row.find_all(['td', 'th'])
                print(f"Header row has {len(header_cells)} cells: {[cell.get_text(strip=True) for cell in header_cells]}")
            
            crew_info = []
            rows = crew_table.find_all('tr')[1:]  # Skip header row

            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                #print(f"Cells: {cells}")
                # Skip rows that don't have enough data or are header rows
                if len(cells) < 13:  # Need at least 13 columns for complete crew data
                    print(f"Skipping row with {len(cells)} cells")
                    continue
                
                # Check if this row contains crew data (should have a number in first cell)
                first_cell = cells[0].get_text(strip=True)
                # Look for crew number pattern (1, 2, 3, etc.)
                if not first_cell.isdigit():
                    print(f"Skipping row with no crew number: {first_cell}")
                    continue
                
                try:
                    # Debug: Log what we're getting from each cell
                    log_info(f"Row cells ({len(cells)}): {[cell.get_text(strip=True) for cell in cells]}")
                    
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
                    
                    # Normalize country names
                    if country == 'Russian Federation':
                        country = 'Russia'
                    
                    # Parse the table row based on the Expedition 73 table structure
                    crew_member = {
                        'name': f"{cells[3].get_text(strip=True)} {cells[2].get_text(strip=True)}",  # Given names + Surname
                        'country': country,  # Nation extracted from flag image
                        'position': cells[4].get_text(strip=True),  # Position
                        'spaceship': cells[5].get_text(strip=True),  # Spacecraft (launch)
                        'launch_date': cells[6].get_text(strip=True),  # Launch date
                        'launch_time': cells[7].get_text(strip=True),  # Launch time
                        'landing_spacecraft': cells[8].get_text(strip=True),  # Spacecraft (landing)
                        'landing_date': cells[9].get_text(strip=True),  # Landing date
                        'landing_time': cells[10].get_text(strip=True),  # Landing time
                        'mission_duration': cells[11].get_text(strip=True),  # Mission duration
                        'orbits': cells[12].get_text(strip=True),  # Orbits
                        'expedition': 'Expedition 73'  # Default expedition
                    }
                    
                    # Debug: Log the parsed crew member data
                    log_info(f"Parsed crew member: {crew_member}")
                    
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
                    if (crew_member['launch_date'] and crew_member['launch_date'].strip() and 
                        crew_member['launch_time'] and crew_member['launch_time'].strip() != 'UTC'):
                        crew_info.append(crew_member)
                        print(f"Added crew member: {crew_member['name']} from {crew_member['country']}")
                    else:
                        if crew_member['launch_time'] and crew_member['launch_time'].strip() == 'UTC':
                            print(f"Skipping future crew member: {crew_member['name']} (launch time not set)")
                        else:
                            print(f"Skipping crew member without launch date: {crew_member['name']}")
                        
                except Exception as e:
                    log_error(f"Error parsing crew member row: {e}")
                    continue
            
            log_info(f"Successfully fetched {len(crew_info)} crew members from Spacefacts.de")
            print(crew_info)
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


# --- Persistence ------------------------------------------------------------ #

def ensure_schema(conn: sqlite3.Connection) -> None:
    """Ensure the database schema exists."""
    try:
        log_info("Creating/updating crew database schema")
        
        # Force recreation of tables to ensure correct schema
        log_info("Recreating database tables to ensure correct schema")
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
                status TEXT DEFAULT 'active'      -- 'active' or 'returned'
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
                status TEXT DEFAULT 'active'
            );
        """)
        conn.commit()
        log_info("Database schema recreated successfully")
        
        # Verify the schema was created correctly
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(crew_members)")
        columns = cursor.fetchall()
        log_info(f"crew_members table has {len(columns)} columns:")
        for col in columns:
            log_info(f"  {col[1]} ({col[2]})")
        
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
        
        log_info(f"Inserting new crew snapshot with {len(crew)} members")
        cur.execute("INSERT INTO snapshots (fetched_at, checksum) VALUES (?, ?)", (fetched_at, checksum))
        snapshot_id = cur.lastrowid

        # Debug: Log the first crew member's data structure
        if crew:
            first_member = crew[0]
            log_info(f"First crew member data: {first_member}")
            log_info(f"Values to insert: snapshot_id={snapshot_id}, name={first_member['name']}, country={first_member['country']}, spaceship={first_member['spaceship']}, expedition={first_member['expedition']}, position={first_member.get('position')}, launch_date={first_member.get('launch_date')}, launch_time={first_member.get('launch_time')}, landing_date={first_member.get('landing_date')}, landing_time={first_member.get('landing_time')}, mission_duration={first_member.get('mission_duration')}, orbits={first_member.get('orbits')}, status={first_member.get('status', 'active')}")
        
        cur.executemany(
            """
            INSERT INTO crew_members (snapshot_id, name, country, spaceship, expedition, position, launch_date, launch_time, landing_spacecraft, landing_date, landing_time, mission_duration, orbits, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (snapshot_id, m["name"], m["country"], m["spaceship"], m["expedition"], 
                 m.get("position"), m.get("launch_date"), m.get("launch_time"), 
                 m.get("landing_spacecraft"), m.get("landing_date"), m.get("landing_time"), m.get("mission_duration"), 
                 m.get("orbits"), m.get("status", "active"))
                for m in crew
            ],
        )

        # Refresh current_crew to mirror this snapshot
        cur.execute("DELETE FROM current_crew")
        cur.executemany(
            """
            INSERT INTO current_crew (name, country, spaceship, expedition, position, launch_date, launch_time, 
                landing_spacecraft, landing_date, landing_time, mission_duration, orbits, status) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [(m["name"], m["country"], m["spaceship"], m["expedition"], 
            m.get("position"), m.get("launch_date"), m.get("launch_time"), 
            m.get("landing_spacecraft"), m.get("landing_date"), m.get("landing_time"),
            m.get("mission_duration"), m.get("orbits"), m.get("status", "active")) for m in crew],
        )


        conn.commit()
        log_info(f"Successfully inserted snapshot {snapshot_id}")
        return snapshot_id
        
    except sqlite3.Error as e:
        log_error(f"Failed to insert crew snapshot: {e}")
        raise

def main() -> int:
    """Main function to fetch and store ISS crew data."""
    try:
        db_path = get_db_path()
        log_info(f"Using database: {db_path}")
        
        # Add timeout to database connection
        conn = sqlite3.connect(db_path, timeout=30.0)
        conn.isolation_level = None  # Enable autocommit mode
        
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
        print("Running in test mode - testing database operations only")
        try:
            db_path = get_db_path()
            print(f"Database path: {db_path}")
            
            conn = sqlite3.connect(db_path, timeout=10.0)
            conn.isolation_level = None
            
            ensure_schema(conn)
            print("Schema created successfully")
            
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
                'status': 'active'
            }]
            
            checksum = compute_checksum(test_crew)
            print(f"Test checksum: {checksum[:8]}...")
            
            insert_snapshot(conn, test_crew, checksum)
            print("Test data inserted successfully")
            
            conn.close()
            print("Test completed successfully")
            sys.exit(0)
            
        except Exception as e:
            print(f"Test failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        sys.exit(main())
