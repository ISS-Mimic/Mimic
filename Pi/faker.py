#!/usr/bin/env python3

"""
telemetry_replay_real_time.py
─────────────────────────────
Replay archived ISS telemetry so that "now" (2025) maps onto the
same clock time one year earlier (2024), then stream forward at real time.

run like: python faker.py /home/pi/Telemetry/2024Jul18 --year 2024

Assumptions
• TXT files live under one root (can be a single-day folder).
• Each TXT line:  <hours-since-Jan-01-yyyy> <value>
• Filename stem == telemetry.ID  (e.g. P1000004.txt)
"""

from __future__ import annotations
import argparse, asyncio, heapq, pathlib, sqlite3, time, sys
from datetime import datetime, timezone, timedelta

DB_PATH   = pathlib.Path("/dev/shm/iss_telemetry.db")
TABLE     = "telemetry"

# ────────────────────────── helpers ────────────────────────────────────────
def hours_to_epoch(year: int, hrs: float) -> float:
    """Convert hour-offset to Unix seconds (UTC)."""
    anchor = datetime(year, 1, 1, tzinfo=timezone.utc)
    return (anchor + timedelta(hours=hrs)).timestamp()

def line_reader(path: pathlib.Path, tid: str, base_year: int, start_ts: float):
    """
    Yield (ts, val, tid) but skip lines BEFORE start_ts so
    the very first record we produce is >= desired anchor.
    """
    with path.open() as f:
        for ln in f:
            if not ln.strip():
                continue
            hrs, val = ln.split(maxsplit=1)
            ts = hours_to_epoch(base_year, float(hrs))
            if ts >= start_ts:          # skip until we reach anchor point
                yield ts, float(val), tid

async def wait_for_table(db_path: pathlib.Path, poll=0.5) -> sqlite3.Connection:
    """Wait until DB file exists *and* table `telemetry` exists."""
    while True:
        if db_path.exists():
            try:
                tmp = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
                ok  = tmp.execute(
                        "SELECT 1 FROM sqlite_master "
                        "WHERE type='table' AND name=? LIMIT 1", (TABLE,)
                      ).fetchone()
                tmp.close()
                if ok:
                    break
            except sqlite3.OperationalError:
                pass
        await asyncio.sleep(poll)

    con = sqlite3.connect(db_path, isolation_level=None)  # autocommit
    con.execute("PRAGMA busy_timeout = 3000;")
    con.execute("PRAGMA journal_mode = WAL;")
    return con

def year_shift(now_utc: datetime, target_year: int) -> datetime:
    """
    Replace the year field but keep month/day/time.
    Handles Feb-29 safely (not relevant for July).
    """
    try:
        return now_utc.replace(year=target_year)
    except ValueError:
        # 29-Feb → 28-Feb fallback
        return now_utc.replace(day=28, year=target_year)

# ───────────────────────── replay coroutine ───────────────────────────────
async def replay(root: pathlib.Path, base_year: int, debug: bool):
    # 1. Determine the target anchor timestamp (one year ago "now")
    now_utc   = datetime.now(timezone.utc)
    start_dt  = year_shift(now_utc, base_year)
    start_ts  = start_dt.timestamp()

    if debug:
        print(f"[replay] Wall-time now UTC : {now_utc}")
        print(f"[replay] Target anchor UTC : {start_dt}")

    # 2. Collect TXT paths
    txt_paths = list(root.rglob("*.txt"))
    if not txt_paths:
        raise SystemExit(f"[replay] No *.txt files under {root}")

    # 3. Wait for Mimic DB & grab valid ID list
    db = await wait_for_table(DB_PATH)
    id_set = {row[0] for row in db.execute(f"SELECT ID FROM {TABLE}")}

    # 4. Map files whose stem matches an ID
    files = {p.stem: p for p in txt_paths if p.stem in id_set}
    if not files:
        raise SystemExit("[replay] No TXT stems match IDs in the telemetry table.")

    # 5. Build iterators that start at start_ts
    streams = {tid: iter(line_reader(p, tid, base_year, start_ts))
               for tid, p in files.items()}

    # Prime heap
    heap: list[tuple[float, float, str]] = []
    for tid, it in streams.items():
        try:
            heapq.heappush(heap, next(it))
        except StopIteration:
            pass
    if not heap:
        print("[replay] Nothing in archive at/after the anchor time.")
        return

    # First record defines anchor pairing between data time and wall time
    t0_data, t0_wall = heap[0][0], time.monotonic()

    UPDATE = (f"UPDATE {TABLE} "
              "   SET Timestamp = ?, Value = ? "
              " WHERE ID = ? "
              "   AND (Timestamp IS NULL OR CAST(Timestamp AS REAL) < ?)")

    while heap:
        if not DB_PATH.exists():
            print("[replay] DB vanished; Mimic quit.")
            return

        ts, val, tid = heapq.heappop(heap)

        # pacing
        delay = (ts - t0_data) - (time.monotonic() - t0_wall)
        if delay > 0:
            await asyncio.sleep(delay)

        ts_str  = f"{ts:.6f}"
        val_str = f"{val:.6f}"
        db.execute(UPDATE, (ts_str, val_str, tid, ts))

        if debug and tid == next(iter(files)):
            print(f"{datetime.utcfromtimestamp(ts)}  {tid}  {val_str}")

        # next record from this stream
        try:
            heapq.heappush(heap, next(streams[tid]))
        except StopIteration:
            pass

# ───────────────────────────── CLI ────────────────────────────────────────
async def main():
    ap = argparse.ArgumentParser(
        description="Replay ISS telemetry in real time, mapping 'now' to same time a year earlier"
    )
    ap.add_argument("root", help="Root folder (or single-day folder) containing TXT files")
    ap.add_argument("--year", type=int, required=True,
                    help="Base year of the recordings (e.g. 2024)")
    ap.add_argument("--debug", action="store_true", help="Verbose prints")
    args = ap.parse_args()

    await replay(pathlib.Path(args.root), args.year, args.debug)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)

