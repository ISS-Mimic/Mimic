#!/usr/bin/env python3
"""
mock_iss_feeder.py — quick-and-dirty ISS Mimic DB fuzzer

Usage examples:
  # Set a few values once:
  python mock_iss_feeder.py --db /dev/shm/iss_telemetry.db --set psarj=12.5 ssarj=33.1 iss_mode=LVLH

  # Stream updates at 5 Hz for selected labels (timestamps auto-updated):
  python mock_iss_feeder.py --db /dev/shm/iss_telemetry.db --loop --hz 5 --set "USGNC_PS_Solar_Beta_Angle=+0.1" "psarj=+1" "ssarj=-1"

  # Load values from JSON (dict of label->value) and apply once:
  python mock_iss_feeder.py --db /dev/shm/iss_telemetry.db --json values.json

Notes:
- The 'telemetry' table is assumed to have columns: Label (PK), Timestamp, Value, ID, dbID.
- Values are stored as TEXT in the schema, so we stringify. Use +N / -N to increment/decrement numerics.
- DBs in /dev/shm are tmpfs; your app's init may recreate them at startup — run this *after* Mimic has created the tables.
"""

import argparse
import datetime as dt
import json
import os
import re
import sqlite3
import sys
import time
from typing import Dict, Tuple

def parse_assignments(items):
    """
    Parse CLI assignments like: label=value
    Supports relative updates: label=+1.5 or label=-2
    Returns dict: label -> ('set'|'inc'|'dec', value_str)
    """
    result: Dict[str, Tuple[str, str]] = {}
    for it in items:
        if '=' not in it:
            raise ValueError(f"Bad --set item '{it}', expected label=value")
        label, value = it.split('=', 1)
        label = label.strip()
        value = value.strip()
        if not label:
            raise ValueError(f"Empty label in '{it}'")
        if re.fullmatch(r'[+-]\s*\d+(\.\d+)?', value):
            mode = 'inc' if value.lstrip().startswith('+') else 'dec'
            # store absolute magnitude as string
            amount = value.lstrip('+-').strip()
            result[label] = (mode, amount)
        else:
            result[label] = ('set', value)
    return result

def open_db(path):
    conn = sqlite3.connect(path, timeout=3.0, isolation_level=None)  # autocommit
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=3000;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

def upsert_value(conn, label, how, value):
    """
    Update one label in telemetry table. If it doesn't exist, warn.
    """
    now = dt.datetime.utcnow().isoformat(timespec='seconds') + 'Z'
    cur = conn.cursor()
    cur.execute("SELECT Value FROM telemetry WHERE Label = ?", (label,))
    row = cur.fetchone()
    if row is None:
        print(f"[warn] Label '{label}' not found; skipping")
        return False

    if how == 'set':
        new_val = str(value)
    else:
        # try numeric math, fallback to string if not numeric
        old = row[0]
        try:
            old_f = float(old)
            delta = float(value)
            if how == 'inc':
                new_val = str(old_f + delta)
            else:
                new_val = str(old_f - delta)
        except Exception:
            print(f"[warn] Label '{label}' has non-numeric value '{old}', can't apply +/-; leaving unchanged")
            return False

    cur.execute(
        "UPDATE telemetry SET Value = ?, Timestamp = ? WHERE Label = ?",
        (new_val, now, label),
    )
    return True

def apply_json(conn, json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("JSON must be an object mapping label -> value")
    count = 0
    for k, v in data.items():
        if upsert_value(conn, k, 'set', v):
            count += 1
    print(f"[ok] Applied {count} assignments from JSON")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="/dev/shm/iss_telemetry.db", help="Path to iss telemetry database")
    ap.add_argument("--set", nargs="*", default=[], help="Assignments like Label=value; supports +N/-N for numeric delta")
    ap.add_argument("--json", help="Path to JSON dict of label->value")
    ap.add_argument("--loop", action="store_true", help="If set, keep applying assignments at HZ rate")
    ap.add_argument("--hz", type=float, default=1.0, help="Loop frequency (default 1 Hz)")
    args = ap.parse_args()

    if not os.path.exists(args.db):
        print(f"[err] DB not found at {args.db}")
        return 2

    conn = open_db(args.db)
    try:
        if args.json:
            apply_json(conn, args.json)

        assignments = parse_assignments(args.set) if args.set else {}

        if assignments and not args.loop:
            count = 0
            for k, (how, val) in assignments.items():
                if upsert_value(conn, k, how, val):
                    count += 1
            print(f"[ok] Applied {count} assignment(s)")
            return 0

        if args.loop:
            period = 1.0 / max(args.hz, 1e-6)
            print(f"[loop] Applying {len(assignments)} assignment(s) every {period:.3f}s — Ctrl+C to stop")
            while True:
                start = time.perf_counter()
                for k, (how, val) in assignments.items():
                    upsert_value(conn, k, how, val)
                elapsed = time.perf_counter() - start
                time.sleep(max(0.0, period - elapsed))

        if not assignments and not args.json:
            print("[note] Nothing to do; use --set and/or --json")
            return 1
    finally:
        conn.close()

if __name__ == "__main__":
    sys.exit(main())
