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

def fetch_iss_crew(max_attempts: int = 3, timeout: int = 15) -> List[Dict[str, str]]:
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

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

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
    FOREIGN KEY(snapshot_id) REFERENCES snapshots(id) ON DELETE CASCADE
);

-- Convenience view/table that always mirrors the latest snapshot, for quick reads:
CREATE TABLE IF NOT EXISTS current_crew (
    name TEXT NOT NULL,
    country TEXT NOT NULL,
    spaceship TEXT NOT NULL,
    expedition TEXT NOT NULL
);
"""

def ensure_schema(conn: sqlite3.Connection) -> None:
    """Ensure the database schema exists."""
    try:
        log_info("Creating/updating crew database schema")
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        log_info("Database schema updated successfully")
    except sqlite3.Error as e:
        log_error(f"Failed to create database schema: {e}")
        raise

def normalize_for_checksum(crew: List[Dict[str, str]]) -> str:
    """
    Build a stable string for checksumming (order-independent).
    """
    normalized = sorted(
        [{k: v.strip() for k, v in member.items()} for member in crew],
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

        cur.executemany(
            """
            INSERT INTO crew_members (snapshot_id, name, country, spaceship, expedition)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (snapshot_id, m["name"], m["country"], m["spaceship"], m["expedition"])
                for m in crew
            ],
        )

        # Refresh current_crew to mirror this snapshot
        cur.execute("DELETE FROM current_crew")
        cur.executemany(
            "INSERT INTO current_crew (name, country, spaceship, expedition) VALUES (?, ?, ?, ?)",
            [(m["name"], m["country"], m["spaceship"], m["expedition"]) for m in crew],
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
        
        conn = sqlite3.connect(db_path)
        conn.isolation_level = None  # Enable autocommit mode
        
        ensure_schema(conn)

        log_info("Fetching current ISS crew data")
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
    sys.exit(main())
