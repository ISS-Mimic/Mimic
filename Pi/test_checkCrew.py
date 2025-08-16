#!/usr/bin/env python3
"""
Fetch current ISS crew from Spacefacts/Wikipedia and store in SQLite.

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
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from functools import lru_cache
from multiprocessing import cpu_count
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from utils.logger import log_info, log_error

WIKI_API_URL = (
    "https://en.wikipedia.org/w/api.php"
    "?action=parse&page=Template:People_currently_in_space&prop=wikitext&format=json"
)

SPACEFACTS_BASE = "https://spacefacts.de/iss/english/"
HEADERS = {
    "User-Agent": "ISS-Mimic Bot (+https://github.com/ISS-Mimic; iss.mimic@gmail.com)"
}

# Precompiled helpers
_RE_ISS_SECTION = re.compile(
    r"International Space Station.*?(?=Tiangong space station|$)",
    re.DOTALL,
)
_RE_WIKILINKS = re.compile(r"\[\[([^\]]+)\]\]")
_RE_COUNTRIES = re.compile(r"size=15px\|([^}\n]+)")
_RE_QUOTES = re.compile(r'"([^"]+)"')


# --------------------------------------------------------------------------- #
# Networking
# --------------------------------------------------------------------------- #

def _build_session() -> requests.Session:
    sess = requests.Session()
    retries = Retry(
        total=4,
        connect=3,
        read=3,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retries, pool_connections=16, pool_maxsize=32)
    sess.mount("http://", adapter)
    sess.mount("https://", adapter)
    sess.headers.update(HEADERS)
    return sess

_SESSION: Optional[requests.Session] = None


def session() -> requests.Session:
    global _SESSION
    if _SESSION is None:
        _SESSION = _build_session()
    return _SESSION


# --------------------------------------------------------------------------- #
# DB path
# --------------------------------------------------------------------------- #

def get_db_path() -> str:
    """Get the database path, prioritizing /dev/shm on Linux."""
    if Path("/dev/shm").is_dir():
        return "/dev/shm/iss_crew.db"
    data_dir = Path.home() / ".mimic_data"
    data_dir.mkdir(exist_ok=True)
    return str(data_dir / "iss_crew.db")


# --------------------------------------------------------------------------- #
# Spacefacts helpers
# --------------------------------------------------------------------------- #

def get_latest_expedition_number() -> int:
    """
    Discover the latest ISS expedition number by probing Spacefacts pages.
    Returns an integer, defaulting to 73 on failure.
    """
    try:
        # Probe downwards from a reasonable upper bound
        # (keeps requests to a minimum once we find the first valid page)
        for exp_num in range(84, 68, -1):  # 84..69
            url = f"{SPACEFACTS_BASE}exp_{exp_num}.htm"
            try:
                r = session().get(url, timeout=6)
                if r.status_code != 200:
                    continue
                soup = BeautifulSoup(r.content, "html.parser")
                page_text = soup.get_text(" ", strip=True).lower()
                if f"expedition {exp_num}" not in page_text and f"exp {exp_num}" not in page_text:
                    continue

                # Expect a table with these headers
                for table in soup.find_all("table"):
                    txt = table.get_text(" ").strip()
                    if all(k in txt for k in ("No.", "Nation", "Surname", "Given names", "Position")):
                        rows = table.find_all("tr")
                        if len(rows) > 1:
                            return exp_num
            except Exception:
                continue
        log_info("Could not determine expedition number, using default: 73")
        return 73
    except Exception as e:
        log_error(f"Error determining latest expedition: {e}")
        return 73


def get_spacefacts_url(expedition_num: Optional[int] = None) -> str:
    if expedition_num is None:
        expedition_num = get_latest_expedition_number()
    return f"{SPACEFACTS_BASE}exp_{expedition_num}.htm"


# --------------------------------------------------------------------------- #
# Astronaut page parsing (single fetch for portrait + mission data)
# --------------------------------------------------------------------------- #

def _parse_astronaut_page(html: bytes, astronaut_page_url: str) -> Tuple[Optional[str], int, int]:
    """
    Return (image_url, total_time_days, current_mission_days) from one HTML page.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Try to find a hi-res portrait link first
    img_url: Optional[str] = None
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "portraits" in href and href.lower().endswith(".jpg"):
            if href.startswith("http"):
                img_url = href
            elif href.startswith("/"):
                img_url = f"https://spacefacts.de{href}"
            else:
                base = "/".join(astronaut_page_url.split("/")[:-1])
                img_url = f"{base}/{href}"
            break

    # Fallback: first non-gif non-flag <img>
    if not img_url:
        for img in soup.find_all("img"):
            src = img.get("src", "")
            if (src and not src.lower().endswith(".gif")
                    and "flag" not in src.lower()):
                if src.startswith("http"):
                    img_url = src
                elif src.startswith("/"):
                    img_url = f"https://spacefacts.de{src}"
                else:
                    base = "/".join(astronaut_page_url.split("/")[:-1])
                    img_url = f"{base}/{src}"
                break

    # Mission table parsing - FIXED VERSION
    total_days = 0
    current_days = 0
    today = datetime.now()

    # Look for the Spaceflights table - more robust search
    spaceflights_header = soup.find(['h3', 'h2'], string=lambda s: s and 'Spaceflights' in s)
    if not spaceflights_header:
        # Try alternative headers
        spaceflights_header = soup.find(['h3', 'h2'], string=lambda s: s and 'spaceflight' in s.lower())
    
    if spaceflights_header:
        table = spaceflights_header.find_next('table')
        if table:
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
                        total_days += mission_duration
                    except ValueError:
                        continue
                else:
                    # Current mission: "08.04.2025" (single date)
                    try:
                        launch_date = datetime.strptime(time_cell.strip(), '%d.%m.%Y')
                        current_mission_days = (today - launch_date).days
                        total_days += current_mission_days
                    except ValueError:
                        continue

    return img_url, total_days, current_days


def _fetch_astronaut_details(url: str) -> Tuple[str, Optional[str], int, int]:
    """
    Download and parse one astronaut page.
    Returns (url, image_url, total_days, current_days).
    """
    try:
        r = session().get(url, timeout=10)
        r.raise_for_status()
        image_url, total_days, current_days = _parse_astronaut_page(r.content, url)
        return url, image_url, total_days, current_days
    except Exception as e:
        log_error(f"Error fetching astronaut details {url}: {e}")
        return url, None, 0, 0


# --------------------------------------------------------------------------- #
# Fetchers
# --------------------------------------------------------------------------- #

def fetch_spacefacts_crew(max_attempts: int = 3, timeout: int = 10) -> List[Dict[str, str]]:
    """
    Fetch detailed crew data from Spacefacts ISS expedition page.
    Returns list of dicts with enhanced crew information.
    """
    expedition_number = get_latest_expedition_number()
    url = get_spacefacts_url(expedition_number)
    log_info(f"Fetching crew data from: {url}")
    
    # Define today for date calculations
    today = datetime.now()

    last_exc = None
    for attempt in range(1, max_attempts + 1):
        try:
            log_info(f"Spacefacts attempt {attempt}/{max_attempts}")
            r = session().get(url, timeout=timeout)
            r.raise_for_status()
            soup = BeautifulSoup(r.content, "html.parser")

            crew_table = None
            for table in soup.find_all("table"):
                txt = table.get_text(" ", strip=True)
                if all(h in txt for h in ("No.", "Nation", "Surname", "Given names", "Position")):
                    crew_table = table
                    break
            if not crew_table:
                log_error("No ISS crew table found on Spacefacts.de")
                return []

            rows = crew_table.find_all("tr")[1:]
            crew_info: List[Dict[str, str]] = []

            # Collect astronaut-page URLs we actually need (one pass)
            astro_pages: List[str] = []
            parsed_rows: List[Tuple[Dict[str, str], Optional[str]]] = []

            for row in rows:
                tds = row.find_all(["td", "th"])
                if len(tds) < 13:
                    continue
                if not tds[0].get_text(strip=True).isdigit():
                    continue

                # Country from flag
                country = "Unknown"
                img = tds[1].find("img")
                if img:
                    country = img.get("title") or img.get("alt") or country
                    if country == "Russian Federation":
                        country = "Russia"

                given_names = tds[3].get_text(strip=True)
                surname = tds[2].get_text(strip=True)

                nn = _RE_QUOTES.search(given_names)
                first_name = nn.group(1) if nn else (given_names.split()[0] if given_names else "")

                # Try to find link to personal page
                astro_url = None
                a = tds[2].find("a", href=True)
                if a:
                    href = a["href"]
                    if href.startswith("http"):
                        astro_url = href
                    elif href.startswith("/"):
                        astro_url = f"https://spacefacts.de{href}"
                    else:
                        # "../../bios/astronauts/english/xxx.htm" style
                        astro_url = f"https://spacefacts.de/bios/{href.split('bios/')[-1]}".replace("../", "")

                # Normalize dates immediately
                def _fmt_date(dot_date: str) -> Optional[str]:
                    if not dot_date:
                        return None
                    s = dot_date.strip()
                    if s.startswith("(") and s.endswith(")"):
                        s = s[1:-1]
                    try:
                        d, m, y = s.split(".")
                        return f"{y}-{m.zfill(2)}-{d.zfill(2)}"
                    except Exception:
                        return None

                launch_date = _fmt_date(tds[6].get_text(strip=True))
                landing_date_raw = tds[9].get_text(strip=True)
                landing_date = _fmt_date(landing_date_raw)
                status = "returned" if landing_date else "active"

                # Orbits numeric
                orbits_txt = tds[12].get_text(strip=True)
                orbits_num = None
                if orbits_txt:
                    digits = "".join(ch for ch in orbits_txt if ch.isdigit())
                    orbits_num = int(digits) if digits else None

                member = {
                    "name": f"{first_name} {surname}".strip(),
                    "country": (country or "Unknown").strip(),
                    "position": tds[4].get_text(strip=True),
                    "spaceship": tds[5].get_text(strip=True),
                    "launch_date": launch_date,
                    "launch_time": tds[7].get_text(strip=True),
                    "landing_spacecraft": tds[8].get_text(strip=True) or None,
                    "landing_date": landing_date,
                    "landing_time": tds[10].get_text(strip=True) or None,
                    "mission_duration": "",  # Will be calculated below
                    "orbits": orbits_num,
                    "expedition": f"Expedition {expedition_number}",
                    "status": status,
                    "image_url": None,                 # to be filled
                    "total_time_in_space": 0,          # to be filled
                    "current_mission_duration": 0,     # to be filled
                }
                
                # Calculate mission duration
                if member["launch_date"]:
                    try:
                        launch_dt = datetime.strptime(member["launch_date"], "%Y-%m-%d")
                        mission_days = (today - launch_dt).days
                        member["mission_duration"] = f"{mission_days}d"
                    except:
                        member["mission_duration"] = ""

                parsed_rows.append((member, astro_url))
                if astro_url:
                    astro_pages.append(astro_url)

            # Fetch astronaut pages concurrently (single pass per astronaut)
            details: Dict[str, Tuple[Optional[str], int, int]] = {}
            if astro_pages:
                unique_pages = list(dict.fromkeys(astro_pages))  # preserve order, dedupe
                max_workers = max(2, min(8, cpu_count() * 5))
                with ThreadPoolExecutor(max_workers=max_workers) as ex:
                    futs = {ex.submit(_fetch_astronaut_details, u): u for u in unique_pages}
                    for fut in as_completed(futs):
                        u, img_url, total_days, current_days = fut.result()
                        details[u] = (img_url, total_days, current_days)

            # Build final list; filter: launched + active + has specific launch time (not just "UTC")
            for member, url_page in parsed_rows:
                if (member["launch_date"] and member["launch_time"] and member["launch_time"].strip() != "UTC"
                        and member["status"] == "active"):
                    if url_page and url_page in details:
                        img_url, total_days, current_days = details[url_page]
                        member["image_url"] = img_url
                        member["total_time_in_space"] = total_days
                        member["current_mission_duration"] = current_days
                    crew_info.append(member)

            log_info(f"Successfully fetched {len(crew_info)} crew members from Spacefacts.de")
            return crew_info

        except requests.RequestException as exc:
            last_exc = exc
            log_error(f"Request failed on attempt {attempt}: {exc}")
        except Exception as exc:
            last_exc = exc
            log_error(f"Unexpected error on attempt {attempt}: {exc}")

    log_error(f"Failed to fetch Spacefacts.de after {max_attempts} attempts: {last_exc}")
    return []


def fetch_iss_crew(max_attempts: int = 3, timeout: int = 10) -> List[Dict[str, str]]:
    """
    Wikipedia fallback. Returns list of dicts: [{name, spaceship, country, expedition}, ...]
    """
    last_exc = None
    for attempt in range(1, max_attempts + 1):
        try:
            log_info(f"Wikipedia attempt {attempt}/{max_attempts}")
            r = session().get(WIKI_API_URL, timeout=timeout)
            r.raise_for_status()
            data = r.json()
            template_content = data["parse"]["wikitext"]["*"]

            m = _RE_ISS_SECTION.search(template_content)
            if not m:
                log_info("No ISS section found in Wikipedia template")
                return []

            iss_section = m.group(0)
            links = _RE_WIKILINKS.findall(iss_section)
            countries = _RE_COUNTRIES.findall(iss_section)

            def clean(tok: str) -> str:
                parts = tok.split("|")
                text = parts[-1].strip()
                return re.sub(r"\s+", " ", text)

            crew_info: List[Dict[str, str]] = []
            current_ship = ""
            expedition = ""
            ci = 0

            for tok in links:
                text = clean(tok)

                if "Expedition" in text:
                    expedition = text
                    continue

                if any(key in text for key in ("SpaceX", "Soyuz", "Axiom", "Boeing")):
                    current_ship = text
                    continue

                country = countries[ci].strip() if ci < len(countries) else "Unknown"
                ci += 1
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
            log_error(f"Request failed on attempt {attempt}: {exc}")

    log_error(f"Failed to fetch ISS crew after {max_attempts} attempts: {last_exc}")
    return []


# --------------------------------------------------------------------------- #
# Checksum helpers
# --------------------------------------------------------------------------- #

def normalize_for_checksum(crew: List[Dict[str, str]]) -> str:
    normalized = sorted(
        [{k: (v.strip() if isinstance(v, str) else v) for k, v in member.items()} for member in crew],
        key=lambda m: (m.get("name", ""), m.get("spaceship", ""), m.get("country", ""), m.get("expedition", "")),
    )
    return json.dumps(normalized, ensure_ascii=False, separators=(",", ":"))


def compute_checksum(crew: List[Dict[str, str]]) -> str:
    return hashlib.sha256(normalize_for_checksum(crew).encode("utf-8")).hexdigest()


def get_last_checksum(conn: sqlite3.Connection) -> Optional[str]:
    try:
        row = conn.execute("SELECT checksum FROM snapshots ORDER BY id DESC LIMIT 1").fetchone()
        return row[0] if row else None
    except sqlite3.Error as e:
        log_error(f"Failed to get last checksum: {e}")
        return None


# --------------------------------------------------------------------------- #
# Persistence
# --------------------------------------------------------------------------- #

def ensure_schema(conn: sqlite3.Connection) -> None:
    """Create tables/indexes if missing (no destructive drops)."""
    cur = conn.cursor()
    cur.executescript("""
        PRAGMA journal_mode=WAL;
        PRAGMA synchronous=NORMAL;

        CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fetched_at TEXT NOT NULL,          -- ISO 8601 UTC
            checksum TEXT NOT NULL UNIQUE
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
            current_mission_duration INTEGER,
            FOREIGN KEY(snapshot_id) REFERENCES snapshots(id)
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

        CREATE INDEX IF NOT EXISTS idx_crew_members_snapshot ON crew_members(snapshot_id);
        CREATE INDEX IF NOT EXISTS idx_crew_members_name ON crew_members(name);
    """)
    conn.commit()


def insert_snapshot(conn: sqlite3.Connection, crew: List[Dict[str, str]], checksum: str) -> int:
    """Insert a new crew snapshot into the database."""
    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    cur = conn.cursor()
    try:
        cur.execute("BEGIN")
        cur.execute("INSERT INTO snapshots (fetched_at, checksum) VALUES (?, ?)", (fetched_at, checksum))
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
                    snapshot_id,
                    m["name"], m["country"], m["spaceship"], m["expedition"],
                    m.get("position"), m.get("launch_date"), m.get("launch_time"),
                    m.get("landing_spacecraft"), m.get("landing_date"), m.get("landing_time"),
                    m.get("mission_duration"), m.get("orbits"), m.get("status", "active"),
                    m.get("image_url"), m.get("total_time_in_space", 0), m.get("current_mission_duration", 0)
                )
                for m in crew
            ],
        )

        # Refresh current_crew to mirror this snapshot
        cur.execute("DELETE FROM current_crew")
        cur.executemany(
            """
            INSERT INTO current_crew (
                name, country, spaceship, expedition, position, launch_date, launch_time,
                landing_spacecraft, landing_date, landing_time, mission_duration, orbits,
                status, image_url, total_time_in_space, current_mission_duration
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    m["name"], m["country"], m["spaceship"], m["expedition"], m.get("position"),
                    m.get("launch_date"), m.get("launch_time"), m.get("landing_spacecraft"),
                    m.get("landing_date"), m.get("landing_time"), m.get("mission_duration"),
                    m.get("orbits"), m.get("status", "active"), m.get("image_url"),
                    m.get("total_time_in_space", 0), m.get("current_mission_duration", 0)
                )
                for m in crew
            ],
        )
        cur.execute("COMMIT")
        log_info(f"Successfully inserted snapshot {snapshot_id}")
        return snapshot_id
    except Exception as e:
        cur.execute("ROLLBACK")
        log_error(f"Failed to insert crew snapshot: {e}")
        raise


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main() -> int:
    try:
        db_path = get_db_path()
        log_info(f"Using database: {db_path}")

        conn = sqlite3.connect(db_path, timeout=30.0)
        ensure_schema(conn)

        log_info("Fetching current ISS crew data from Spacefacts.de")
        crew = fetch_spacefacts_crew()

        if not crew:
            log_info("Spacefacts fetch failed/empty, falling back to Wikipedia")
            crew = fetch_iss_crew()

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
            session().close()
        except Exception:
            pass
        try:
            # Close DB last for cleaner logs
            if "conn" in locals():
                conn.close()
                log_info("Database connection closed")
        except Exception as e:
            log_error(f"Error closing database connection: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        try:
            db_path = get_db_path()
            conn = sqlite3.connect(db_path, timeout=10.0)
            ensure_schema(conn)

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
        except Exception:
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        sys.exit(main())
