#!/usr/bin/env python3
"""
Fetch current ISS crew from Wikipedia/Spacefacts and store in SQLite.

- Runs once and exits (subprocess-friendly).
- Creates schema on first run (idempotent).
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
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

from utils.logger import log_info, log_error

WIKI_API_URL = (
    "https://en.wikipedia.org/w/api.php"
    "?action=parse&page=Template:People_currently_in_space&prop=wikitext&format=json"
)

# ------------------------- Precompiled regexes ------------------------------

RE_NICKNAME = re.compile(r'"([^"]+)"')
RE_WIKILINK = re.compile(r"\[\[([^\]]+)\]\]")
RE_COUNTRY = re.compile(r"size=15px\|([^}\n]+)")
RE_SECTION = re.compile(
    r"International Space Station.*?(?=Tiangong space station|$)",
    re.DOTALL
)

# ------------------------- HTTP session helper ------------------------------

def make_session() -> requests.Session:
    s = requests.Session()
    retries = Retry(
        total=4, connect=3, read=3, backoff_factor=0.5,
        status_forcelist=(500, 502, 503, 504),
        allowed_methods=frozenset(["GET", "HEAD"]),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retries, pool_connections=10, pool_maxsize=10)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    s.headers.update({
        "User-Agent": "ISS-Mimic Bot (+https://github.com/ISS-Mimic; iss.mimic@gmail.com)",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    })
    return s

# ------------------------- DB path ------------------------------------------

def get_db_path() -> str:
    """Get the database path, prioritizing /dev/shm on Linux."""
    if Path("/dev/shm").exists() and Path("/dev/shm").is_dir():
        return "/dev/shm/iss_crew.db"
    else:
        # Windows fallback
        data_dir = Path.home() / ".mimic_data"
        data_dir.mkdir(exist_ok=True)
        return str(data_dir / "iss_crew.db")

# ------------------------- Network / scraping -------------------------------

def get_latest_expedition_number(session: requests.Session) -> int:
    """
    Discover the latest ISS expedition number by checking Spacefacts.de.
    Returns the expedition number as an integer.
    """
    base_url = "https://spacefacts.de/iss/english/"

    def is_valid_expedition_page(soup, expected_exp_num):
        """Check if the page actually contains data for the expected expedition number."""
        page_text = str(soup).lower()
        if f"expedition {expected_exp_num}" not in page_text and f"exp {expected_exp_num}" not in page_text:
            return False
        tables = soup.find_all('table')
        for table in tables:
            table_text = str(table)
            if ('No.' in table_text and 'Nation' in table_text and 'Surname' in table_text and
                'Given names' in table_text and 'Position' in table_text):
                rows = table.find_all('tr')
                if len(rows) > 1:
                    return True
        return False

    try:
        # Try a reasonable range (adjust if needed)
        for exp_num in range(73, 85):  # 73..84
            test_url = f"{base_url}exp_{exp_num}.htm"
            try:
                r = session.get(test_url, timeout=5)
                if r.status_code == 200:
                    soup = BeautifulSoup(r.content, 'lxml')
                    if is_valid_expedition_page(soup, exp_num):
                        return exp_num
            except Exception:
                continue

        # fallback a bit lower
        for exp_num in range(72, 69, -1):  # 72..70
            test_url = f"{base_url}exp_{exp_num}.htm"
            try:
                r = session.get(test_url, timeout=5)
                if r.status_code == 200:
                    soup = BeautifulSoup(r.content, 'lxml')
                    if is_valid_expedition_page(soup, exp_num):
                        return exp_num
            except Exception:
                continue

        log_info("Could not determine expedition number, using default: 73")
        return 73

    except Exception as e:
        log_error(f"Error determining latest expedition: {e}")
        return 73

def get_spacefacts_url(expedition_num: int | None = None) -> str:
    if expedition_num is None:
        # Note: main() determines with a session; this fallback is unused there.
        expedition_num = 73
    return f"https://spacefacts.de/iss/english/exp_{expedition_num}.htm"

def _country_from_flag_cell(country_cell) -> str:
    """Extract country name from a flag <img> within a cell."""
    country = "Unknown"
    img = country_cell.find('img')
    if img:
        country = img.get('title', img.get('alt', 'Unknown'))
        if country == 'Unknown':
            src = img.get('src', '') or ''
            # crude filename fallbacks
            mapping = {
                'usa.gif': 'USA', 'russia.gif': 'Russia', 'japan.gif': 'Japan',
                'canada.gif': 'Canada', 'china.gif': 'China', 'gb.gif': 'United Kingdom',
                'italy.gif': 'Italy', 'france.gif': 'France', 'germany.gif': 'Germany',
                'netherlands.gif': 'Netherlands', 'sweden.gif': 'Sweden', 'norway.gif': 'Norway',
                'denmark.gif': 'Denmark', 'poland.gif': 'Poland', 'belgium.gif': 'Belgium',
                'spain.gif': 'Spain'
            }
            for key, val in mapping.items():
                if key in src.lower():
                    country = val
                    break
    if country == 'Russian Federation':
        country = 'Russia'
    return country

def _name_from_given_and_surname(given_names: str, surname: str) -> str:
    """Prefer nickname in quotes; else first given name."""
    m = RE_NICKNAME.search(given_names)
    first = m.group(1) if m else (given_names.split()[0] if given_names else "")
    return f"{first} {surname}".strip()

def _abs_url_from_relative(base_page: str, href: str) -> Optional[str]:
    if not href:
        return None
    if href.startswith('http'):
        return href
    if href.startswith('/'):
        return f"https://spacefacts.de{href}"
    if href.startswith('..'):
        # handle "../../bios/category/lang/file.htm"
        parts = href.split('/')
        if len(parts) >= 4:
            category = parts[3]  # astronauts/cosmonauts/international
            language = parts[4] if len(parts) > 4 else 'english'
            filename = parts[-1]
            return f"https://spacefacts.de/bios/{category}/{language}/{filename}"
        return None
    # relative to base dir
    base = '/'.join(base_page.split('/')[:-1])
    return f"{base}/{href}"

def fetch_spacefacts_crew(session: requests.Session, max_attempts: int = 3, timeout: int = 10) -> List[Dict[str, str]]:
    """
    Build base rows (no slow per-astronaut enrichment yet).
    Returns list of dicts.
    """
    expedition_number = get_latest_expedition_number(session)
    log_info(f"Found expedition number: {expedition_number}")
    current_url = get_spacefacts_url(expedition_number)
    log_info(f"Fetching crew data from: {current_url}")

    last_exc = None
    for attempt in range(max_attempts):
        try:
            log_info(f"Attempting Spacefacts fetch (attempt {attempt + 1}/{max_attempts})")
            r = session.get(current_url, timeout=timeout)
            r.raise_for_status()
            soup = BeautifulSoup(r.content, 'lxml')

            tables = soup.find_all('table')
            crew_table = None
            for table in tables:
                table_text = str(table)
                if ('No.' in table_text and 'Nation' in table_text and 'Surname' in table_text and
                    'Given names' in table_text and 'Position' in table_text):
                    crew_table = table
                    break

            if not crew_table:
                log_error("No ISS crew table found on Spacefacts.de")
                return []

            base_rows: List[Dict[str, str]] = []
            rows = crew_table.find_all('tr')[1:]  # skip header

            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) < 13:
                    continue
                first_cell = cells[0].get_text(strip=True)
                if not first_cell.isdigit():
                    continue

                try:
                    country = _country_from_flag_cell(cells[1])
                    given_names = cells[3].get_text(strip=True)
                    surname = cells[2].get_text(strip=True)
                    full_name = _name_from_given_and_surname(given_names, surname)

                    # astronaut page url (for enrichment later)
                    astronaut_page_url = None
                    surname_cell = cells[2]
                    if surname_cell.find('a'):
                        href = surname_cell.find('a').get('href', '')
                        astronaut_page_url = _abs_url_from_relative(current_url, href)

                    # build row
                    row_dict: Dict[str, Optional[str | int]] = {
                        'name': full_name,
                        'country': country,
                        'position': cells[4].get_text(strip=True),
                        'spaceship': cells[5].get_text(strip=True),
                        'launch_date': cells[6].get_text(strip=True),
                        'launch_time': cells[7].get_text(strip=True),
                        'landing_spacecraft': cells[8].get_text(strip=True),
                        'landing_date': cells[9].get_text(strip=True),
                        'landing_time': cells[10].get_text(strip=True),
                        'mission_duration': '',  # computed elsewhere if needed
                        'orbits': cells[12].get_text(strip=True),
                        'expedition': f"Expedition {expedition_number}",
                        'status': 'active',
                        'astronaut_page_url': astronaut_page_url,
                    }

                    # normalize launch_date (DD.MM.YYYY -> YYYY-MM-DD)
                    if row_dict['launch_date']:
                        try:
                            day, month, year = str(row_dict['launch_date']).split('.')
                            row_dict['launch_date'] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                        except Exception:
                            row_dict['launch_date'] = None
                    else:
                        row_dict['launch_date'] = None

                    # landing_date normalization + status
                    if row_dict['landing_date'] and row_dict['landing_date'] not in ['', '(??.01.2026)', '(09.12.2025)']:
                        try:
                            ld = str(row_dict['landing_date'])
                            if ld.startswith('(') and ld.endswith(')'):
                                date_part = ld[1:-1]
                                if '.' in date_part:
                                    d, m, y = date_part.split('.')
                                    row_dict['landing_date'] = f"{y}-{m.zfill(2)}-{d.zfill(2)}"
                                    row_dict['status'] = 'active'
                                else:
                                    row_dict['landing_date'] = None
                                    row_dict['status'] = 'active'
                            else:
                                d, m, y = ld.split('.')
                                row_dict['landing_date'] = f"{y}-{m.zfill(2)}-{d.zfill(2)}"
                                row_dict['status'] = 'returned'
                        except Exception:
                            row_dict['landing_date'] = None
                            row_dict['status'] = 'active'
                    else:
                        row_dict['landing_date'] = None
                        row_dict['status'] = 'active'

                    # orbits numeric
                    try:
                        orbits_text = str(row_dict['orbits']).strip()
                        row_dict['orbits'] = int(''.join(filter(str.isdigit, orbits_text))) if orbits_text else None
                    except Exception:
                        row_dict['orbits'] = None

                    # Only include launched & active
                    if (row_dict['launch_date'] and str(row_dict['launch_date']).strip() and
                        row_dict['launch_time'] and str(row_dict['launch_time']).strip() != 'UTC' and
                        row_dict['status'] == 'active'):
                        base_rows.append(row_dict)  # enrichment later

                except Exception as e:
                    log_error(f"Error parsing crew member row: {e}")
                    continue

            log_info(f"Successfully fetched {len(base_rows)} crew members (base rows) from Spacefacts.de")
            return base_rows

        except requests.RequestException as exc:
            last_exc = exc
            log_error(f"Request failed on attempt {attempt + 1}: {exc}")
        except Exception as exc:
            last_exc = exc
            log_error(f"Unexpected error on attempt {attempt + 1}: {exc}")

    log_error(f"Failed to fetch Spacefacts.de crew data after {max_attempts} attempts: {last_exc}")
    return []

def fetch_iss_crew(session: requests.Session, max_attempts: int = 3, timeout: int = 10) -> List[Dict[str, str]]:
    """
    Wikipedia fallback. Returns base rows (no slow enrichment).
    """
    last_exc = None
    for attempt in range(max_attempts):
        try:
            log_info(f"Attempting to fetch ISS crew via Wikipedia (attempt {attempt + 1}/{max_attempts})")
            r = session.get(WIKI_API_URL, timeout=timeout)
            r.raise_for_status()
            data = r.json()
            template_content = data["parse"]["wikitext"]["*"]

            m = RE_SECTION.search(template_content)
            if not m:
                log_info("No ISS section found in Wikipedia template")
                return []

            iss_section = m.group(0)
            links = RE_WIKILINK.findall(iss_section)
            countries = RE_COUNTRY.findall(iss_section)

            crew_info: List[Dict[str, str]] = []
            current_ship = ""
            expedition = ""
            country_idx = 0

            def clean_link_token(tok: str) -> str:
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

                # astronaut name
                country = countries[country_idx].strip() if country_idx < len(countries) else "Unknown"
                country_idx += 1
                crew_info.append(
                    {
                        "name": text,
                        "spaceship": current_ship or "Unknown",
                        "country": country,
                        "expedition": expedition or "Unknown",
                        "position": None,
                        "launch_date": None,
                        "launch_time": None,
                        "landing_spacecraft": None,
                        "landing_date": None,
                        "landing_time": None,
                        "mission_duration": "",
                        "orbits": None,
                        "status": "active",
                        "astronaut_page_url": None,
                    }
                )

            log_info(f"Successfully fetched {len(crew_info)} crew members (Wikipedia base rows)")
            return crew_info

        except requests.RequestException as exc:
            last_exc = exc
            log_error(f"Request failed on attempt {attempt + 1}: {exc}")

    error_msg = f"Failed to fetch ISS crew via Wikipedia after {max_attempts} attempts: {last_exc}"
    log_error(error_msg)
    return []

def get_astronaut_image_url(session: requests.Session, astronaut_page_url: str) -> Optional[str]:
    """
    Extract the astronaut's image URL from their personal page.
    Returns the direct image URL or None if not found.
    """
    if not astronaut_page_url:
        return None

    try:
        r = session.get(astronaut_page_url, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, 'lxml')

        # Look for hi-res portrait links first
        portrait_links = soup.find_all('a', href=re.compile(r'portraits.*\.jpg'))
        if portrait_links:
            for link in portrait_links:
                href = link.get('href', '')
                if not href:
                    continue
                if href.startswith('http'):
                    return href
                if href.startswith('/'):
                    return f"https://spacefacts.de{href}"
                # map relative hi-res by category inferred from page url
                if 'bios/' in astronaut_page_url:
                    category = astronaut_page_url.split('bios/')[1].split('/')[0]
                    filename = href.split('/')[-1]
                    if category == 'cosmonauts':
                        return f"https://spacefacts.de/bios/portraits_hi/cosmonauts/{filename}"
                    elif category == 'astronauts':
                        return f"https://spacefacts.de/bios/portraits2/astronauts/{filename}"
                    else:
                        return f"https://spacefacts.de/bios/portraits_hi/{category}/{filename}"

        # Fallback: first plausible <img>
        images = soup.find_all('img')
        for img in images:
            src = img.get('src', '')
            if not src or src.lower().endswith('.gif') or 'flag' in src.lower():
                continue
            if src.startswith('http'):
                return src
            if src.startswith('/'):
                return f"https://spacefacts.de{src}"
            base = '/'.join(astronaut_page_url.split('/')[:-1])
            return f"{base}/{src}"

        return None

    except Exception as e:
        log_error(f"Error fetching astronaut image from {astronaut_page_url}: {e}")
        return None

def get_astronaut_mission_data(session: requests.Session, astronaut_page_url: str) -> dict:
    """
    Extract mission data from the astronaut's Spaceflights table.
    Returns dict with total_time_in_space and current_mission_duration (days).
    """
    if not astronaut_page_url:
        return {'total_time_in_space': 0, 'current_mission_duration': 0}

    try:
        r = session.get(astronaut_page_url, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, 'lxml')

        spaceflights_header = soup.find('h3', string='Spaceflights')
        if not spaceflights_header:
            return {'total_time_in_space': 0, 'current_mission_duration': 0}

        table = spaceflights_header.find_next('table')
        if not table:
            return {'total_time_in_space': 0, 'current_mission_duration': 0}

        total_time = 0
        current_mission_days = 0
        today = datetime.now()

        rows = table.find_all('tr')[1:]
        for row in rows:
            cells = row.find_all('td')
            if len(cells) < 5:
                continue
            if 'Total' in str(cells[0]):
                continue
            mission_cell = cells[1].get_text(strip=True)
            if not mission_cell:
                continue
            time_cell = cells[3].get_text(strip=True)
            if not time_cell:
                continue

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
                # Current mission: "08.04.2025"
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

# ------------------------- Persistence --------------------------------------

def ensure_schema(conn: sqlite3.Connection) -> None:
    """Ensure the database schema exists (no dropping)."""
    cur = conn.cursor()
    # Pragmas once per connection
    cur.execute("PRAGMA journal_mode=WAL;")
    cur.execute("PRAGMA synchronous=NORMAL;")
    cur.execute("PRAGMA temp_store=MEMORY;")
    cur.execute("PRAGMA mmap_size=134217728;")  # 128 MiB

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fetched_at TEXT NOT NULL,          -- ISO 8601 UTC
            checksum TEXT NOT NULL UNIQUE      -- checksum of normalized payload
        );

        CREATE TABLE IF NOT EXISTS crew_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id INTEGER NOT NULL,
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
            image_url TEXT,
            total_time_in_space INTEGER,
            current_mission_duration INTEGER
        );

        CREATE TABLE IF NOT EXISTS current_crew (
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
            image_url TEXT,
            total_time_in_space INTEGER,
            current_mission_duration INTEGER
        );

        -- tiny cache for astronaut-page enrichment
        CREATE TABLE IF NOT EXISTS astronaut_cache (
            page_url TEXT PRIMARY KEY,
            image_url TEXT,
            total_time_in_space INTEGER,
            current_mission_duration INTEGER,
            updated_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_snapshots_id ON snapshots(id);
        CREATE INDEX IF NOT EXISTS idx_current_crew_name ON current_crew(name);
    """)
    conn.commit()

def normalize_for_checksum(crew: List[Dict[str, object]]) -> str:
    """
    Build a stable string for checksumming (order-independent).
    """
    normalized = sorted(
        [{k: (v.strip() if isinstance(v, str) else v) for k, v in member.items()} for member in crew],
        key=lambda m: (m.get("name"), m.get("spaceship"), m.get("country"), m.get("expedition")),
    )
    return json.dumps(normalized, ensure_ascii=False, separators=(",", ":"))

def compute_checksum(crew: List[Dict[str, object]]) -> str:
    norm = normalize_for_checksum(crew)
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()

def compute_light_checksum(base_rows: List[Dict[str, object]]) -> str:
    """
    Only identity/stable fields—skip enrichment so we can short-circuit quickly.
    """
    minimal = [
        {
            "name": r.get("name"),
            "country": r.get("country"),
            "spaceship": r.get("spaceship"),
            "expedition": r.get("expedition"),
            "position": r.get("position"),
            "launch_date": r.get("launch_date"),
            "launch_time": r.get("launch_time"),
            "landing_spacecraft": r.get("landing_spacecraft"),
            "landing_date": r.get("landing_date"),
            "landing_time": r.get("landing_time"),
            "orbits": r.get("orbits"),
            "status": r.get("status", "active"),
        }
        for r in base_rows
    ]
    minimal = sorted(minimal, key=lambda m: (m.get("name"), m.get("spaceship"), m.get("country"), m.get("expedition")))
    return hashlib.sha256(json.dumps(minimal, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()

def get_last_checksum(conn: sqlite3.Connection) -> Optional[str]:
    try:
        row = conn.execute("SELECT checksum FROM snapshots ORDER BY id DESC LIMIT 1").fetchone()
        return row[0] if row else None
    except sqlite3.Error as e:
        log_error(f"Failed to get last checksum: {e}")
        return None

# --------- enrichment cache (24h TTL) ---------------------------------------

CACHE_TTL_HOURS = 24

def cache_get(conn: sqlite3.Connection, page_url: Optional[str]) -> Optional[dict]:
    if not page_url:
        return None
    row = conn.execute(
        "SELECT image_url, total_time_in_space, current_mission_duration, updated_at "
        "FROM astronaut_cache WHERE page_url = ?;", (page_url,)
    ).fetchone()
    if not row:
        return None
    image_url, total_time, current_days, updated = row
    try:
        updated_dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
    except Exception:
        return None
    if datetime.now(timezone.utc) - updated_dt > timedelta(hours=CACHE_TTL_HOURS):
        return None
    return {
        "image_url": image_url,
        "total_time_in_space": total_time or 0,
        "current_mission_duration": current_days or 0
    }

def cache_put(conn: sqlite3.Connection, page_url: str, data: dict) -> None:
    conn.execute(
        """
        INSERT INTO astronaut_cache(page_url, image_url, total_time_in_space, current_mission_duration, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(page_url) DO UPDATE SET
          image_url=excluded.image_url,
          total_time_in_space=excluded.total_time_in_space,
          current_mission_duration=excluded.current_mission_duration,
          updated_at=excluded.updated_at;
        """,
        (
            page_url, data.get("image_url"),
            data.get("total_time_in_space", 0),
            data.get("current_mission_duration", 0),
            datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        )
    )

def enrich_crew(session: requests.Session, conn: sqlite3.Connection, base_rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    def work(row: Dict[str, object]) -> Dict[str, object]:
        page = row.get("astronaut_page_url")
        # try cache first
        cached = cache_get(conn, page)
        if cached:
            row.update({
                "image_url": cached.get("image_url"),
                "total_time_in_space": cached.get("total_time_in_space", 0),
                "current_mission_duration": cached.get("current_mission_duration", 0),
            })
            return row

        # fetch if we have a page
        if page:
            img = get_astronaut_image_url(session, str(page))
            md = get_astronaut_mission_data(session, str(page))
            row.update({
                "image_url": img,
                "total_time_in_space": md.get("total_time_in_space", 0),
                "current_mission_duration": md.get("current_mission_duration", 0),
            })
            try:
                cache_put(conn, str(page), {
                    "image_url": row.get("image_url"),
                    "total_time_in_space": row.get("total_time_in_space", 0),
                    "current_mission_duration": row.get("current_mission_duration", 0),
                })
            except Exception as e:
                log_error(f"cache_put failed: {e}")
        else:
            row.setdefault("image_url", None)
            row.setdefault("total_time_in_space", 0)
            row.setdefault("current_mission_duration", 0)
        return row

    # modest pool size to respect remote site
    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = [ex.submit(work, dict(r)) for r in base_rows]
        out: List[Dict[str, object]] = []
        for f in as_completed(futures):
            out.append(f.result())
    return out

def insert_snapshot(conn: sqlite3.Connection, crew: List[Dict[str, object]], checksum: str) -> int:
    """Insert a new crew snapshot into the database (single transaction)."""
    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    cur = conn.cursor()
    cur.execute("BEGIN IMMEDIATE;")
    try:
        cur.execute("INSERT INTO snapshots (fetched_at, checksum) VALUES (?, ?);", (fetched_at, checksum))
        snapshot_id = cur.lastrowid

        cur.executemany(
            """
            INSERT INTO crew_members (
                snapshot_id, name, country, spaceship, expedition, position,
                launch_date, launch_time, landing_spacecraft, landing_date, landing_time,
                mission_duration, orbits, status, image_url, total_time_in_space, current_mission_duration
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    snapshot_id, m["name"], m["country"], m["spaceship"], m["expedition"],
                    m.get("position"), m.get("launch_date"), m.get("launch_time"),
                    m.get("landing_spacecraft"), m.get("landing_date"), m.get("landing_time"),
                    m.get("mission_duration"), m.get("orbits"), m.get("status", "active"),
                    m.get("image_url"), m.get("total_time_in_space", 0), m.get("current_mission_duration", 0)
                )
                for m in crew
            ],
        )

        # refresh current_crew atomically
        cur.execute("DELETE FROM current_crew;")
        cur.executemany(
            """
            INSERT INTO current_crew (
                name, country, spaceship, expedition, position, launch_date, launch_time,
                landing_spacecraft, landing_date, landing_time, mission_duration, orbits, status,
                image_url, total_time_in_space, current_mission_duration
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            [
                (
                    m["name"], m["country"], m["spaceship"], m["expedition"],
                    m.get("position"), m.get("launch_date"), m.get("launch_time"),
                    m.get("landing_spacecraft"), m.get("landing_date"), m.get("landing_time"),
                    m.get("mission_duration"), m.get("orbits"), m.get("status", "active"),
                    m.get("image_url"), m.get("total_time_in_space", 0), m.get("current_mission_duration", 0)
                )
                for m in crew
            ],
        )

        conn.commit()
        log_info(f"Successfully inserted snapshot {snapshot_id}")
        return snapshot_id
    except Exception as e:
        conn.rollback()
        log_error(f"Failed to insert crew snapshot: {e}")
        raise

# ------------------------- Main ---------------------------------------------

def main() -> int:
    """Main function to fetch and store ISS crew data."""
    try:
        db_path = get_db_path()
        log_info(f"Using database: {db_path}")

        conn = sqlite3.connect(db_path, timeout=30.0, isolation_level=None)
        ensure_schema(conn)

        session = make_session()

        log_info("Fetching current ISS crew data from Spacefacts.de (base rows)")
        base_rows = fetch_spacefacts_crew(session)

        # If Spacefacts.de fails, fall back to Wikipedia
        if not base_rows:
            log_info("Spacefacts.de fetch failed, falling back to Wikipedia")
            base_rows = fetch_iss_crew(session)

        # If fetch returns empty, still handle checksum+write so app can notice change.
        light_ck = compute_light_checksum(base_rows)
        last = get_last_checksum(conn)

        if last == light_ck:
            log_info("No changes in crew identities; skipping enrichment & DB write")
            return 0

        # Enrich only when identities changed
        log_info("Crew identities changed; enriching with astronaut pages (parallel + cache)")
        crew = enrich_crew(session, conn, base_rows)

        # Final checksum includes enriched fields
        checksum = compute_checksum(crew)
        if last == checksum:
            log_info("No net changes after enrichment")
            return 0

        log_info("Inserting new snapshot")
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

# ------------------------- CLI ----------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        try:
            db_path = get_db_path()
            conn = sqlite3.connect(db_path, timeout=10.0, isolation_level=None)
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
