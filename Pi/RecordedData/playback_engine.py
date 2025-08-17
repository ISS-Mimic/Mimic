#!/usr/bin/env python3
"""
ISS Telemetry Playback Engine

Reads recorded telemetry data from text files and feeds it into the database
at controlled playback speeds. Each telemetry ID has its own file with
timestamp and value columns.

Usage:
    python playback_engine.py <data_folder> <playback_speed> [--loop]
    
Examples:
    python playback_engine.py HTV 10          # Play HTV data at 10x speed
    python playback_engine.py OFT2 60         # Play OFT2 data at 60x speed
    python playback_engine.py HTV 20 --loop   # Loop HTV data at 20x speed
"""

import argparse
import os
import sys
import time
import sqlite3
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import signal
import threading

# Add the parent directory to the path so we can import utils
sys.path.append(str(Path(__file__).parent.parent))
try:
    from utils.logger import log_info, log_error
except ImportError:
    # Fallback if utils.logger not available
    def log_info(msg): print(f"INFO: {msg}")
    def log_error(msg): print(f"ERROR: {msg}")

class PlaybackEngine:
    """Engine for playing back recorded telemetry data."""
    
    def __init__(self, data_folder: str, playback_speed: float, loop: bool = False):
        print(f"Initializing PlaybackEngine with folder: {data_folder}, speed: {playback_speed}, loop: {loop}")
        
        self.data_folder = Path(data_folder)
        self.playback_speed = playback_speed
        self.loop = loop
        self.running = False
        self.paused = False
        
        # Database path
        self.db_path = self._get_db_path()
        print(f"Using database: {self.db_path}")
        
        # Data storage - Updated for string IDs
        self.telemetry_data: Dict[str, List[Tuple[float, float]]] = {}
        self.current_indices: Dict[str, int] = {}
        self.start_time: Optional[float] = None
        
        # Signal handling for clean shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        print("PlaybackEngine initialized successfully")
        
    def _get_db_path(self) -> str:
        """Get the telemetry database path."""
        # Try /dev/shm first (Linux), then fallback to local
        if Path("/dev/shm").exists():
            return "/dev/shm/iss_telemetry.db"
        else:
            # Windows fallback
            data_dir = Path.home() / ".mimic_data"
            data_dir.mkdir(exist_ok=True)
            return str(data_dir / "iss_telemetry.db")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        print(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
    
    def load_data(self) -> bool:
        """Load all telemetry data from the specified folder."""
        try:
            print(f"Checking if data folder exists: {self.data_folder}")
            if not self.data_folder.exists():
                print(f"ERROR: Data folder not found: {self.data_folder}")
                return False
            
            print(f"Loading telemetry data from: {self.data_folder}")
            
            # Find all telemetry files
            telemetry_files = list(self.data_folder.glob("*.txt"))
            print(f"Found {len(telemetry_files)} telemetry files: {[f.name for f in telemetry_files]}")
            
            if not telemetry_files:
                print(f"ERROR: No telemetry files found in {self.data_folder}")
                return False
            
            # Load each telemetry file
            for file_path in telemetry_files:
                try:
                    print(f"Processing file: {file_path.name}")
                    
                    # Extract telemetry ID from filename
                    telemetry_id = self._extract_telemetry_id(file_path.name)
                    if telemetry_id is None:
                        print(f"ERROR: Could not extract telemetry ID from filename: {file_path.name}")
                        continue
                    
                    print(f"Extracted telemetry ID: {telemetry_id}")
                    
                    # Load the data
                    data = self._load_telemetry_file(file_path)
                    if data:
                        self.telemetry_data[telemetry_id] = data
                        self.current_indices[telemetry_id] = 0
                        print(f"Loaded {len(data)} data points for telemetry ID {telemetry_id}")
                        print(f"First few data points: {data[:3]}")
                    else:
                        print(f"WARNING: No data loaded from {file_path.name}")
                    
                except Exception as e:
                    print(f"ERROR: Error loading file {file_path}: {e}")
                    continue
            
            if not self.telemetry_data:
                print("ERROR: No valid telemetry data loaded")
                return False
            
            print(f"Successfully loaded {len(self.telemetry_data)} telemetry streams")
            print(f"Telemetry IDs: {list(self.telemetry_data.keys())}")
            return True
            
        except Exception as e:
            print(f"ERROR: Error loading data: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # ---------------------------------------------------------------- Telemetry ID extraction - Updated for strings
    def _extract_telemetry_id(self, filename: str) -> Optional[str]:
        """Extract telemetry ID from filename."""
        try:
            # Remove .txt extension and return the alphanumeric ID
            telemetry_id = filename.replace('.txt', '')
            print(f"Extracted telemetry ID: {telemetry_id}")
            return telemetry_id
        except Exception as e:
            print(f"ERROR extracting telemetry ID from {filename}: {e}")
            return None
    
    def _load_telemetry_file(self, file_path: Path) -> List[Tuple[float, float]]:
        """Load telemetry data from a single file."""
        data = []
        
        try:
            print(f"Opening file: {file_path}")
            with open(file_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    try:
                        # Parse timestamp and value
                        parts = line.split()
                        if len(parts) >= 2:
                            timestamp = float(parts[0])
                            value = float(parts[1])
                            data.append((timestamp, value))
                        else:
                            print(f"WARNING: Invalid line format at line {line_num}: {line}")
                            
                    except ValueError as e:
                        print(f"WARNING: Error parsing line {line_num}: {line} - {e}")
                        continue
            
            print(f"Loaded {len(data)} data points from {file_path.name}")
            
            # Sort by timestamp
            data.sort(key=lambda x: x[0])
            print(f"Sorted data, timestamp range: {data[0][0] if data else 'N/A'} to {data[-1][0] if data else 'N/A'}")
            return data
            
        except Exception as e:
            print(f"ERROR: Error reading file {file_path}: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def start(self):
        """Start the playback engine."""
        print("Starting playback engine...")
        
        if not self.telemetry_data:
            print("ERROR: No data loaded, cannot start playback")
            return False
        
        try:
            print(f"Starting playback at {self.playback_speed}x speed")
            self.running = True
            self.start_time = time.time()
            
            # Start playback thread
            print("Starting playback thread...")
            playback_thread = threading.Thread(target=self._playback_loop, daemon=True)
            playback_thread.start()
            
            print("Playback thread started, entering main loop...")
            
            # Wait for completion or interruption
            try:
                while self.running and playback_thread.is_alive():
                    time.sleep(0.1)
                    if time.time() - self.start_time > 1:  # Print status every second
                        elapsed = time.time() - self.start_time
                        print(f"Playback running for {elapsed:.1f} seconds...")
                        self.start_time = time.time()  # Reset timer
                        
            except KeyboardInterrupt:
                print("Playback interrupted by user")
                self.stop()
            
            print("Playback engine finished")
            return True
            
        except Exception as e:
            print(f"ERROR: Error starting playback: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _playback_loop(self):
        """Main playback loop."""
        print("Entering playback loop...")
        try:
            loop_count = 0
            while self.running and not self.paused:
                current_time = time.time()
                elapsed_real_time = current_time - self.start_time
                
                # Calculate what timestamp we should be at
                target_timestamp = elapsed_real_time * self.playback_speed
                
                # Print status every 100 loops
                loop_count += 1
                if loop_count % 100 == 0:
                    print(f"Playback loop: elapsed={elapsed_real_time:.1f}s, target_timestamp={target_timestamp:.1f}")
                
                # Update all telemetry streams
                all_complete = True
                for telemetry_id, data in self.telemetry_data.items():
                    if not self._update_telemetry_stream(telemetry_id, data, target_timestamp):
                        all_complete = False
                
                # Check if we've reached the end
                if all_complete:
                    if self.loop:
                        print("Reached end of data, looping...")
                        self._reset_playback()
                    else:
                        print("Playback complete")
                        self.running = False
                        break
                
                # Sleep for a short interval
                time.sleep(0.01)  # 100Hz update rate
                
        except Exception as e:
            print(f"ERROR: Error in playback loop: {e}")
            import traceback
            traceback.print_exc()
            self.running = False
    
    # ---------------------------------------------------------------- Type hints updated
    def _update_telemetry_stream(self, telemetry_id: str, data: List[Tuple[float, float]], 
                                target_timestamp: float) -> bool:
        """Update a single telemetry stream."""
        try:
            current_index = self.current_indices[telemetry_id]
            
            # Find the next data point to send
            while current_index < len(data):
                timestamp, value = data[current_index]
                
                if timestamp <= target_timestamp:
                    # Send this data point
                    self._send_telemetry_value(telemetry_id, value)
                    current_index += 1
                    self.current_indices[telemetry_id] = current_index
                else:
                    # We haven't reached this timestamp yet
                    break
            
            # Return True if we've sent all data for this stream
            return current_index >= len(data)
            
        except Exception as e:
            print(f"ERROR: Error updating telemetry stream {telemetry_id}: {e}")
            return True  # Mark as complete on error
    
    def _verify_database_update(self, telemetry_id: str, value: float):
        """Verify that the database was updated correctly."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT Value, Timestamp FROM telemetry WHERE ID = ?",
                    (telemetry_id,)
                )
                result = cursor.fetchone()
                if result:
                    db_value, db_timestamp = result
                    print(f"DB VERIFY: ID={telemetry_id}, DB Value={db_value}, DB Timestamp={db_timestamp}")
                else:
                    print(f"DB VERIFY: ID={telemetry_id} not found in database!")
                    
        except Exception as e:
            print(f"ERROR: Could not verify database update: {e}")

    def _send_telemetry_value(self, telemetry_id: str, value: float):
        """Send a telemetry value to the database."""
        try:
            print(f"TELEMETRY: ID={telemetry_id}, Value={value}")
            
            # Write to database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE telemetry SET Value = ?, Timestamp = ? WHERE ID = ?",
                    (str(value), datetime.now().isoformat(), telemetry_id)
                )
                conn.commit()
                
            # Verify the update
            self._verify_database_update(telemetry_id, value)
                
        except Exception as e:
            print(f"ERROR: Error sending telemetry value {telemetry_id}={value}: {e}")
    
    def _reset_playback(self):
        """Reset playback to start for looping."""
        print("Resetting playback to beginning...")
        self.start_time = time.time()
        for telemetry_id in self.current_indices:
            self.current_indices[telemetry_id] = 0
        print("Playback reset to beginning")
    
    def pause(self):
        """Pause playback."""
        self.paused = True
        print("Playback paused")
    
    def resume(self):
        """Resume playback."""
        self.paused = False
        print("Playback resumed")
    
    def stop(self):
        """Stop playback."""
        print("Stopping playback...")
        self.running = False
        print("Playback stopped")

def main():
    """Main entry point."""
    print("=== ISS Telemetry Playback Engine ===")
    
    parser = argparse.ArgumentParser(description='ISS Telemetry Playback Engine')
    parser.add_argument('data_folder', help='Folder containing telemetry data files')
    parser.add_argument('playback_speed', type=float, help='Playback speed multiplier (e.g., 10 for 10x)')
    parser.add_argument('--loop', action='store_true', help='Loop playback when reaching end')
    parser.add_argument('--db-path', help='Custom database path')
    
    args = parser.parse_args()
    
    print(f"Arguments: folder={args.data_folder}, speed={args.playback_speed}, loop={args.loop}")
    
    # Validate arguments
    if args.playback_speed <= 0:
        print("ERROR: Playback speed must be positive")
        sys.exit(1)
    
    # Create and run playback engine
    print("Creating playback engine...")
    engine = PlaybackEngine(args.data_folder, args.playback_speed, args.loop)
    
    if args.db_path:
        engine.db_path = args.db_path
        print(f"Using custom database path: {args.db_path}")
    
    # Load data
    print("Loading telemetry data...")
    if not engine.load_data():
        print("ERROR: Failed to load telemetry data")
        sys.exit(1)
    
    # Start playback
    print("Starting playback...")
    if not engine.start():
        print("ERROR: Failed to start playback")
        sys.exit(1)
    
    print("Playback engine finished normally")

if __name__ == "__main__":
    main()
