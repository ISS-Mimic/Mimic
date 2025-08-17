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
from utils.logger import log_info, log_error

class PlaybackEngine:
    """Engine for playing back recorded telemetry data."""
    
    def __init__(self, data_folder: str, playback_speed: float, loop: bool = False):
        self.data_folder = Path(data_folder)
        self.playback_speed = playback_speed
        self.loop = loop
        self.running = False
        self.paused = False
        
        # Database path
        self.db_path = self._get_db_path()
        
        # Data storage
        self.telemetry_data: Dict[int, List[Tuple[float, float]]] = {}
        self.current_indices: Dict[int, int] = {}
        self.start_time: Optional[float] = None
        
        # Signal handling for clean shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
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
        log_info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
    
    def load_data(self) -> bool:
        """Load all telemetry data from the specified folder."""
        try:
            if not self.data_folder.exists():
                log_error(f"Data folder not found: {self.data_folder}")
                return False
            
            log_info(f"Loading telemetry data from: {self.data_folder}")
            
            # Find all telemetry files
            telemetry_files = list(self.data_folder.glob("*.txt"))
            if not telemetry_files:
                log_error(f"No telemetry files found in {self.data_folder}")
                return False
            
            # Load each telemetry file
            for file_path in telemetry_files:
                try:
                    # Extract telemetry ID from filename
                    telemetry_id = self._extract_telemetry_id(file_path.name)
                    if telemetry_id is None:
                        log_error(f"Could not extract telemetry ID from filename: {file_path.name}")
                        continue
                    
                    # Load the data
                    data = self._load_telemetry_file(file_path)
                    if data:
                        self.telemetry_data[telemetry_id] = data
                        self.current_indices[telemetry_id] = 0
                        log_info(f"Loaded {len(data)} data points for telemetry ID {telemetry_id}")
                    
                except Exception as e:
                    log_error(f"Error loading file {file_path}: {e}")
                    continue
            
            if not self.telemetry_data:
                log_error("No valid telemetry data loaded")
                return False
            
            log_info(f"Successfully loaded {len(self.telemetry_data)} telemetry streams")
            return True
            
        except Exception as e:
            log_error(f"Error loading data: {e}")
            return False
    
    def _extract_telemetry_id(self, filename: str) -> Optional[int]:
        """Extract telemetry ID from filename."""
        try:
            # Remove .txt extension and convert to int
            telemetry_id = int(filename.replace('.txt', ''))
            return telemetry_id
        except ValueError:
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
                            log_error(f"Invalid line format at line {line_num}: {line}")
                            
                    except ValueError as e:
                        log_error(f"Error parsing line {line_num}: {line} - {e}")
                        continue
            
            # Sort by timestamp
            data.sort(key=lambda x: x[0])
            return data
            
        except Exception as e:
            log_error(f"Error reading file {file_path}: {e}")
            return []
    
    def start(self):
        """Start the playback engine."""
        if not self.telemetry_data:
            log_error("No data loaded, cannot start playback")
            return False
        
        try:
            log_info(f"Starting playback at {self.playback_speed}x speed")
            self.running = True
            self.start_time = time.time()
            
            # Start playback thread
            playback_thread = threading.Thread(target=self._playback_loop, daemon=True)
            playback_thread.start()
            
            # Wait for completion or interruption
            try:
                while self.running and playback_thread.is_alive():
                    time.sleep(0.1)
            except KeyboardInterrupt:
                log_info("Playback interrupted by user")
                self.stop()
            
            return True
            
        except Exception as e:
            log_error(f"Error starting playback: {e}")
            return False
    
    def _playback_loop(self):
        """Main playback loop."""
        try:
            while self.running and not self.paused:
                current_time = time.time()
                elapsed_real_time = current_time - self.start_time
                
                # Calculate what timestamp we should be at
                target_timestamp = elapsed_real_time * self.playback_speed
                
                # Update all telemetry streams
                all_complete = True
                for telemetry_id, data in self.telemetry_data.items():
                    if not self._update_telemetry_stream(telemetry_id, data, target_timestamp):
                        all_complete = False
                
                # Check if we've reached the end
                if all_complete:
                    if self.loop:
                        log_info("Reached end of data, looping...")
                        self._reset_playback()
                    else:
                        log_info("Playback complete")
                        self.running = False
                        break
                
                # Sleep for a short interval
                time.sleep(0.01)  # 100Hz update rate
                
        except Exception as e:
            log_error(f"Error in playback loop: {e}")
            self.running = False
    
    def _update_telemetry_stream(self, telemetry_id: int, data: List[Tuple[float, float]], 
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
            log_error(f"Error updating telemetry stream {telemetry_id}: {e}")
            return True  # Mark as complete on error
    
    def _send_telemetry_value(self, telemetry_id: int, value: float):
        """Send a telemetry value to the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Update the telemetry value in the database
                cursor.execute(
                    "UPDATE telemetry SET Value = ?, Timestamp = ? WHERE id = ?",
                    (value, datetime.now().isoformat(), telemetry_id)
                )
                
                conn.commit()
                
        except Exception as e:
            log_error(f"Error sending telemetry value {telemetry_id}={value}: {e}")
    
    def _reset_playback(self):
        """Reset playback to start for looping."""
        self.start_time = time.time()
        for telemetry_id in self.current_indices:
            self.current_indices[telemetry_id] = 0
        log_info("Playback reset to beginning")
    
    def pause(self):
        """Pause playback."""
        self.paused = True
        log_info("Playback paused")
    
    def resume(self):
        """Resume playback."""
        self.paused = False
        log_info("Playback resumed")
    
    def stop(self):
        """Stop playback."""
        self.running = False
        log_info("Playback stopped")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='ISS Telemetry Playback Engine')
    parser.add_argument('data_folder', help='Folder containing telemetry data files')
    parser.add_argument('playback_speed', type=float, help='Playback speed multiplier (e.g., 10 for 10x)')
    parser.add_argument('--loop', action='store_true', help='Loop playback when reaching end')
    parser.add_argument('--db-path', help='Custom database path')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.playback_speed <= 0:
        log_error("Playback speed must be positive")
        sys.exit(1)
    
    # Create and run playback engine
    engine = PlaybackEngine(args.data_folder, args.playback_speed, args.loop)
    
    if args.db_path:
        engine.db_path = args.db_path
    
    # Load data
    if not engine.load_data():
        log_error("Failed to load telemetry data")
        sys.exit(1)
    
    # Start playback
    if not engine.start():
        log_error("Failed to start playback")
        sys.exit(1)
    
    log_info("Playback engine finished")

if __name__ == "__main__":
    main()
