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
        print(f"Initializing PlaybackEngine: {data_folder} at {playback_speed}x speed")
        
        self.data_folder = Path(data_folder)
        self.playback_speed = playback_speed
        self.loop = loop
        self.running = False
        self.paused = False
        
        # Database path
        self.db_path = self._get_db_path()
        
        # Data storage
        self.telemetry_data: Dict[str, List[Tuple[float, float]]] = {}
        self.current_indices: Dict[str, int] = {}
        self.start_time: Optional[float] = None
        
        # Initialize update counter
        self._update_count = 0
        
        # Signal handling for clean shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        print("PlaybackEngine ready")
    
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
            if not self.data_folder.exists():
                print(f"ERROR: Data folder not found: {self.data_folder}")
                return False
            
            print(f"Loading data from: {self.data_folder}")
            
            # Find all telemetry files
            telemetry_files = list(self.data_folder.glob("*.txt"))
            if not telemetry_files:
                print(f"ERROR: No telemetry files found in {self.data_folder}")
                return False
            
            # Load each telemetry file
            for file_path in telemetry_files:
                try:
                    # Extract telemetry ID from filename
                    telemetry_id = self._extract_telemetry_id(file_path.name)
                    if telemetry_id is None:
                        print(f"ERROR: Could not extract telemetry ID from filename: {file_path.name}")
                        continue
                    
                    # Load the data
                    data = self._load_telemetry_file(file_path)
                    if data:
                        self.telemetry_data[telemetry_id] = data
                        self.current_indices[telemetry_id] = 0
                    else:
                        print(f"WARNING: No data loaded from {file_path.name}")
                    
                except Exception as e:
                    print(f"ERROR: Error loading file {file_path}: {e}")
                    continue
            
            if not self.telemetry_data:
                print("ERROR: No valid telemetry data loaded")
                return False
            
            print(f"Loaded {len(self.telemetry_data)} telemetry streams")
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
            return telemetry_id
        except Exception as e:
            print(f"ERROR extracting telemetry ID from {filename}: {e}")
            return None
    
    def _load_telemetry_file(self, file_path: Path) -> List[Tuple[float, float]]:
        """Load telemetry data from a single file."""
        data = []
        
        try:
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
            
            if data:
                # Sort by timestamp
                data.sort(key=lambda x: x[0])
                
                # Normalize timestamps to start at 0
                first_timestamp = data[0][0]
                normalized_data = []
                for timestamp, value in data:
                    normalized_timestamp = timestamp - first_timestamp
                    normalized_data.append((normalized_timestamp, value))
                
                print(f"DEBUG: {file_path.name} - original range: {first_timestamp:.6f} to {data[-1][0]:.6f} hours")
                print(f"DEBUG: {file_path.name} - normalized range: 0.000000 to {normalized_data[-1][0]:.6f} hours")
                
                return normalized_data
            else:
                return []
            
        except Exception as e:
            print(f"ERROR: Error reading file {file_path}: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def start(self):
        """Start the playback engine."""
        if not self.telemetry_data:
            print("ERROR: No data loaded, cannot start playback")
            return False
        
        try:
            print(f"Starting playback at {self.playback_speed}x speed")
            
            # Test database connection first
            print("Testing database connection...")
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM telemetry")
                    count = cursor.fetchone()[0]
                    print(f"Database connected successfully. Found {count} telemetry records.")
                    
                    # Test a simple update using the correct method
                    print("Testing database write...")
                    cursor.execute("SELECT Label FROM telemetry WHERE ID = 'S6000004'")
                    result = cursor.fetchone()
                    if result:
                        label = result[0]
                        cursor.execute("UPDATE telemetry SET Value = 'TEST456' WHERE Label = ?", (label,))
                        conn.commit()
                        print(f"Test update completed for Label '{label}'")
                    else:
                        print("Could not find S6000004 record")
                    
            except Exception as e:
                print(f"WARNING: Database connection test failed: {e}")
            
            self.running = True
            self.start_time = time.time()
            
            # Start playback thread
            playback_thread = threading.Thread(target=self._playback_loop, daemon=True)
            playback_thread.start()
            
            print("Playback started - press Ctrl+C to stop")
            
            # Wait for completion or interruption
            try:
                while self.running and playback_thread.is_alive():
                    time.sleep(0.1)
                        
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
        try:
            loop_count = 0
            while self.running and not self.paused:
                current_time = time.time()
                elapsed_real_time = current_time - self.start_time
                
                # Calculate what timestamp we should be at (in fractional hours)
                # Convert elapsed seconds to hours, then multiply by playback speed
                target_timestamp_hours = (elapsed_real_time * self.playback_speed) / 3600.0
                
                # Print status every 1000 loops (about every 10 seconds at 100Hz)
                loop_count += 1
                if loop_count % 1000 == 0:
                    print(f"Playback: {elapsed_real_time:.1f}s elapsed, target={target_timestamp_hours:.6f} hours")
                    
                    # Show some sample telemetry values being sent
                    if self.telemetry_data:
                        sample_id = list(self.telemetry_data.keys())[0]
                        sample_data = self.telemetry_data[sample_id]
                        current_idx = self.current_indices[sample_id]
                        if current_idx < len(sample_data):
                            timestamp, value = sample_data[current_idx]
                            print(f"Sample: {sample_id} = {value:.2f} (at {timestamp:.6f} hours)")
                
                # Update all telemetry streams
                all_complete = True
                for telemetry_id, data in self.telemetry_data.items():
                    if not self._update_telemetry_stream(telemetry_id, data, target_timestamp_hours):
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
            print(f"DEBUG: Updating {telemetry_id} = {value}")
            
            # Write to database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # First, find the record by ID and get its Label (primary key)
                cursor.execute("SELECT Label FROM telemetry WHERE ID = ?", (telemetry_id,))
                result = cursor.fetchone()
                
                if result:
                    label = result[0]
                    
                    # Update just the Value (no timestamp needed)
                    cursor.execute(
                        "UPDATE telemetry SET Value = ? WHERE Label = ?",
                        (str(value), label)
                    )
                    
                    rows_affected = cursor.rowcount
                    print(f"DEBUG: Updated {telemetry_id} to {value} (affected {rows_affected} rows)")
                    conn.commit()
                    
                else:
                    print(f"ERROR: No record found with ID '{telemetry_id}'")
                
            # Increment update counter
            self._update_count += 1
                
            # Show every update for now
            print(f"DB Update: {self._update_count} values sent to database")
                
        except Exception as e:
            print(f"ERROR: Error sending telemetry value {telemetry_id}={value}: {e}")
            import traceback
            traceback.print_exc()
    
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
    
    # Validate arguments
    if args.playback_speed <= 0:
        print("ERROR: Playback speed must be positive")
        sys.exit(1)
    
    # Create and run playback engine
    engine = PlaybackEngine(args.data_folder, args.playback_speed, args.loop)
    
    if args.db_path:
        engine.db_path = args.db_path
    
    # Load data
    if not engine.load_data():
        print("ERROR: Failed to load telemetry data")
        sys.exit(1)
    
    # Start playback
    if not engine.start():
        print("ERROR: Failed to start playback")
        sys.exit(1)
    
    print("Playback engine finished normally")

if __name__ == "__main__":
    main()
