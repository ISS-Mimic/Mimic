#!/usr/bin/env python3
"""
ISS Telemetry Playback Engine (Python, C++-equivalent)

Replays recorded telemetry from a folder of text files into an SQLite database,
mirroring the behavior of `mimic-fakedata.cpp`:

- Anchors playback time to the **earliest** timestamp across all streams.
- Merges all samples into a single time-ordered stream (like a C++ multimap).
- Updates `telemetry.Value` by `ID` as time advances.
- Paces loop at ~100 ms with an accelerated real-time factor.

Usage (match your current workflow):
    python playback_engine.py <data_folder> [playback_speed] [--loop] [--db-path PATH] [--discover]

Examples:
    python playback_engine.py HTV 10
    python playback_engine.py OFT2 60 --loop
    python playback_engine.py ./data 60 --db-path /dev/shm/iss_telemetry.db

Notes:
- By default we use the same **hard-coded** telemetry ID list as the C++ tool.
  If your folder has a different set of files and you want to include every
  `*.txt` present, pass `--discover` to scan dynamically.
- File format: each `<ID>.txt` contains lines with `timestamp value` (space-separated).
  Timestamps are **hours** (floats allowed).
"""

import argparse
import heapq
import signal
import sqlite3
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# --- IDs used by the original C++ playback tool ---
HARD_CODED_IDS = [
     "AIRLOCK000001",  "AIRLOCK000002",  "AIRLOCK000003",  "AIRLOCK000004",  "AIRLOCK000005",
  "AIRLOCK000006",  "AIRLOCK000007",  "AIRLOCK000008",  "AIRLOCK000009",  "AIRLOCK000010",
  "AIRLOCK000011",  "AIRLOCK000012",  "AIRLOCK000013",  "AIRLOCK000014",  "AIRLOCK000015",
  "AIRLOCK000016",  "AIRLOCK000017",  "AIRLOCK000018",  "AIRLOCK000049",  "AIRLOCK000054",
  "AIRLOCK000054",  "AIRLOCK000055",  "AIRLOCK000056",  "AIRLOCK000057",  "NODE2000001",
  "NODE2000002",  "NODE2000006",  "NODE2000007",  "NODE3000004",  "NODE3000005",  "NODE3000008",
  "NODE3000009",  "NODE3000011",  "NODE3000012",  "NODE3000013",  "NODE3000017",  "NODE3000019",
  "P1000001",  "P1000002",  "P1000003",  "P1000004",  "P1000005",  "P4000001",  "P4000002",
  "P4000004",  "P4000005",  "P4000007",  "P4000008",  "P6000001",  "P6000002",  "P6000004",
  "P6000005",  "P6000007",  "P6000008",  "S0000001",  "S0000002",  "S0000003",  "S0000004",
  "S0000005",  "S0000008",  "S0000009",  "S1000001",  "S1000002",  "S1000003",  "S1000004",
  "S1000005",  "S4000001",  "S4000002",  "S4000004",  "S4000005",  "S4000007",  "S4000008",
  "S6000001",  "S6000002",  "S6000004",  "S6000005",  "S6000007",  "S6000008",  "USLAB000006",
  "USLAB000007",  "USLAB000008",  "USLAB000009",  "USLAB000010",  "USLAB000016",  "USLAB000018",
  "USLAB000019",  "USLAB000020",  "USLAB000021",  "USLAB000022",  "USLAB000023",  "USLAB000024",
  "USLAB000025",  "USLAB000026",  "USLAB000027",  "USLAB000028",  "USLAB000029",  "USLAB000030",
  "USLAB000031",  "USLAB000032",  "USLAB000033",  "USLAB000034",  "USLAB000035",  "USLAB000036",
  "USLAB000037",  "USLAB000038",  "USLAB000040",  "USLAB000043",  "USLAB000044",  "USLAB000045",
  "USLAB000046",  "USLAB000047",  "USLAB000048",  "USLAB000049",  "USLAB000050",  "USLAB000051",
  "USLAB000052",  "USLAB000053",  "USLAB000054",  "USLAB000055",  "USLAB000056",  "USLAB000057",
  "USLAB000058",  "USLAB000059",  "USLAB000060",  "USLAB000061",  "USLAB000081",  "USLAB000082",
  "USLAB000083",  "USLAB000084",  "USLAB000095",  "USLAB000096",  "USLAB000097",  "USLAB000102",
  "Z1000001",  "Z1000002",  "Z1000003",  "Z1000004",  "Z1000005",  "Z1000006",  "Z1000007",
  "Z1000008",  "Z1000009",  "Z1000010",  "Z1000011",  "Z1000012",  "Z1000013",  "Z1000014",
  "Z1000015",  "CSAMT000001",  "CSAMT000002",  "CSASSRMS001",  "CSASSRMS002",  "CSASSRMS003",
  "CSASSRMS004",  "CSASSRMS005",  "CSASSRMS006",  "CSASSRMS007",  "CSASSRMS008",  "CSASSRMS009",
  "CSASSRMS010",  "CSASSRMS011",  "CSASPDM0001",  "CSASPDM0002",  "CSASPDM0003",  "CSASPDM0004",
  "CSASPDM0005",  "CSASPDM0006",  "CSASPDM0007",  "CSASPDM0008",  "CSASPDM0009",  "CSASPDM0010",
  "CSASPDM0011",  "CSASPDM0012",  "CSASPDM0013",  "CSASPDM0014",  "CSASPDM0015",  "CSASPDM0016",
  "CSASPDM0017",  "CSASPDM0018",  "CSASPDM0019",  "CSASPDM0020",  "CSASPDM0021",  "CSASPDM0022",
  "CSAMBS00001",  "CSAMBS00002", "CSAMBA00003",  "CSAMBA00004"
]


class Options:
    def __init__(self, data_folder: Path, playback_speed: float = 60.0, loop: bool = False,
                 db_path: Optional[Path] = None, discover: bool = False) -> None:
        self.data_folder = data_folder
        self.playback_speed = playback_speed
        self.loop = loop
        self.db_path = db_path
        self.discover = discover


class PlaybackEngine:
    """Replay recorded telemetry into SQLite, matching the C++ semantics."""

    def __init__(self, opts: Options) -> None:
        self.opts = opts
        self.running: bool = False
        self.paused: bool = False

        # Data: per-ID time series and a merged event heap
        self.telemetry_data: Dict[str, List[Tuple[float, float]]] = {}
        self.events: List[Tuple[float, int, str, float]] = []  # (time, seq, id, value)
        self.data_epoch: Optional[float] = None

        # For diagnostics
        self._update_count: int = 0

    # ------------- Public API -------------

    def load_data(self) -> bool:
        """Load telemetry from <data_folder> and prepare the merged schedule."""
        folder = self.opts.data_folder
        if not folder.exists() or not folder.is_dir():
            print(f"ERROR: Data folder not found: {folder}");
            return False

        ids: List[str]
        if self.opts.discover:
            ids = sorted([p.stem for p in folder.glob("*.txt")])
            if not ids:
                print(f"ERROR: No .txt files found in {folder} (discover mode).");
                return False
        else:
            # Only include files that exist in the folder, preserving C++ list order
            ids = [i for i in HARD_CODED_IDS if (folder / f"{i}.txt").exists()]
            if not ids:
                print("ERROR: None of the hard-coded C++ IDs were found in the folder.")
                return False

        self.telemetry_data.clear()
        total_samples = 0
        for tid in ids:
            series = self._load_telemetry_file(folder / f"{tid}.txt")
            if series:
                self.telemetry_data[tid] = series
                total_samples += len(series)

        if not self.telemetry_data:
            print("ERROR: No valid telemetry data parsed.")
            return False

        # Compute earliest timestamp across all streams
        firsts = [series[0][0] for series in self.telemetry_data.values() if series]
        if not firsts:
            print("ERROR: No timestamps found in any telemetry files.")
            return False
        self.data_epoch = min(firsts)

        # Build a single min-heap of (timestamp, tie_seq, id, value).
        # Tie-break with insertion sequence that mimics the C++ behavior:
        # the C++ inserts all samples of the first ID, then the next, ...
        # so equal-time samples from earlier IDs should come out first.
        self.events.clear()
        seq = 0
        for tid in ids:
            series = self.telemetry_data.get(tid, [])
            for (t, v) in series:
                self.events.append((t, seq, tid, v))
                seq += 1
        heapq.heapify(self.events)

        print(f"Loaded {len(self.telemetry_data)} streams, {total_samples} samples; earliest t={self.data_epoch} h")
        return True

    def start(self) -> bool:
        if not self.events or self.data_epoch is None:
            print("ERROR: Data not loaded. Call load_data() first.")
            return False

        print(f"Starting playback at {self.opts.playback_speed}x speed; loop={self.opts.loop}; DB={self._get_db_path()}")        
        self.running = True
        self.paused = False

        try:
            # Run in the current thread (simpler for a CLI tool).
            self._playback_loop()
            return True
        finally:
            self.running = False

    def stop(self) -> None:
        self.running = False

    def pause(self) -> None:
        self.paused = True

    def resume(self) -> None:
        self.paused = False

    # ------------- Internals -------------

    def _load_telemetry_file(self, file_path: Path) -> List[Tuple[float, float]]:
        """Load a single file. Do NOT normalize timestamps."""
        out: List[Tuple[float, float]] = []
        try:
            with file_path.open("r", encoding="utf-8", errors="replace") as f:
                for line_num, raw in enumerate(f, 1):
                    line = raw.strip()
                    if not line or line.startswith('#'):
                        continue
                    parts = line.split()
                    if len(parts) < 2:
                        print(f"WARNING: Bad line ({file_path.name}:{line_num}): {line}")
                        continue
                    try:
                        t = float(parts[0])  # hours
                        v = float(parts[1])
                    except ValueError:
                        print(f"WARNING: Parse error ({file_path.name}:{line_num}): {line}")
                        continue
                    out.append((t, v))
        except FileNotFoundError:
            # silently skip missing, caller decides
            return []
        except Exception as e:
            print(f"ERROR: Reading {file_path} failed: {e}")
            return []

        # Ensure ordering by timestamp (important for tie-seq semantics)
        out.sort(key=lambda x: x[0])
        return out

    def _get_db_path(self) -> Path:
        if self.opts.db_path:
            return self.opts.db_path
        shm = Path("/dev/shm/iss_telemetry.db")
        if shm.exists() or shm.parent.exists():
            return shm
        return Path.cwd() / "iss_telemetry.db"

    def _playback_loop(self) -> None:
        # Open DB in autocommit mode to mirror C++ sqlite3_exec behavior
        db_path = self._get_db_path()
        conn = sqlite3.connect(str(db_path), isolation_level=None, timeout=5.0, check_same_thread=True)
        try:
            cur = conn.cursor()
            # Fast pragmas (safe on RAM disk; adjust if needed)
            try:
                cur.execute("PRAGMA journal_mode=MEMORY;")
                cur.execute("PRAGMA synchronous=OFF;")
                cur.execute("PRAGMA temp_store=MEMORY;")
                cur.execute("PRAGMA busy_timeout=5000;")
            except Exception:
                pass

            update_sql = "UPDATE telemetry SET Value = ? WHERE ID = ?"

            # Local working heap
            heap: List[Tuple[float, int, str, float]] = list(self.events)
            heapq.heapify(heap)

            program_epoch = time.monotonic()

            while self.running:
                if self.paused:
                    time.sleep(0.1)
                    continue

                # Compute simulated 'now' anchored to earliest data timestamp
                elapsed = time.monotonic() - program_epoch  # seconds
                now_ts = self.data_epoch + (self.opts.playback_speed * elapsed) / 3600.0

                # Flush all due events
                wrote = False
                while heap and heap[0][0] <= now_ts:
                    t, seq, tid, val = heapq.heappop(heap)
                    try:
                        cur.execute(update_sql, (float(val), tid))
                        self._update_count += 1
                    except sqlite3.Error as e:
                        print(f"ERROR: DB update failed for ID={tid} at t={t}: {e}");
                    wrote = True

                # Done?
                if not heap:
                    if self.opts.loop:
                        # rebuild for loop
                        heap = list(self.events)
                        heapq.heapify(heap)
                        program_epoch = time.monotonic()
                        continue
                    else:
                        break

                # Match C++ pacing
                time.sleep(0.1)

            print(f"Playback complete. Total updates: {self._update_count}.")
        finally:
            try:
                conn.close()
            except Exception:
                pass


# ------------- CLI -------------

def parse_args(argv: List[str]) -> Options:
    p = argparse.ArgumentParser(description="ISS telemetry playback (Python, C++-equivalent)")
    p.add_argument("data_folder", type=Path, help="Folder containing <ID>.txt files")
    p.add_argument("playback_speed", type=float, nargs='?', default=60.0,
                   help="Acceleration factor (e.g., 60 for 60x). Default: 60.")
    p.add_argument("--loop", action="store_true", help="Loop playback when finished")
    p.add_argument("--db-path", type=Path, default=None, help="SQLite DB path (default: /dev/shm/iss_telemetry.db or ./iss_telemetry.db)")
    p.add_argument("--discover", action="store_true", help="Discover all *.txt files instead of the hard-coded C++ ID list")
    args = p.parse_args(argv)

    return Options(
        data_folder=args.data_folder,
        playback_speed=args.playback_speed,
        loop=args.loop,
        db_path=args.db_path,
        discover=args.discover,
    )


def main(argv: Optional[List[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    opts = parse_args(argv)

    engine = PlaybackEngine(opts)

    # Clean shutdown on Ctrl+C
    def handle_sigint(sig, frame):
        print("\nSIGINT received: stopping...")
        engine.stop()
    signal.signal(signal.SIGINT, handle_sigint)

    if not engine.load_data():
        return 2

    ok = engine.start()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
