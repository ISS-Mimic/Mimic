#!/usr/bin/python

# Test active TDRS circles with real database data
import sqlite3
from pathlib import Path
import time

def create_real_tdrs_data():
    """Create realistic TDRS data in the database."""
    print("Creating realistic TDRS data:")
    
    # Use Pi path for database
    tdrs_db_path = Path("/dev/shm/tdrs.db")
    if not tdrs_db_path.parent.exists():
        tdrs_db_path = Path.home() / ".mimic_data" / "tdrs.db"
        tdrs_db_path.parent.mkdir(exist_ok=True)
    
    # Create database with realistic data
    conn = sqlite3.connect(str(tdrs_db_path))
    cursor = conn.cursor()
    
    # Create table
    cursor.execute("CREATE TABLE IF NOT EXISTS tdrs (TDRS1 TEXT, TDRS2 TEXT, Timestamp TEXT)")
    
    # Insert realistic data - TDRS 6 and 11 as active
    cursor.execute("INSERT OR REPLACE INTO tdrs VALUES(?, ?, ?)", 
                  ('6', '11', '2024-01-01 12:00:00'))
    
    conn.commit()
    conn.close()
    
    print(f"Database updated at: {tdrs_db_path}")
    print("Active TDRS: TDRS6, TDRS11")

def test_orbit_screen_active_tdrs():
    """Test the orbit screen's active TDRS functionality."""
    print("\nTesting orbit screen active TDRS functionality:")
    
    try:
        from Screens.orbit_screen import Orbit_Screen
        
        # Create orbit screen instance
        orbit_screen = Orbit_Screen()
        
        # Test reading active TDRS
        orbit_screen.update_active_tdrs()
        
        print(f"Active TDRS from orbit screen: {orbit_screen.active_tdrs}")
        
        # Test which TDRS should show circles
        tdrs_ids = [6, 7, 8, 10, 11, 12]
        for tdrs_id in tdrs_ids:
            is_active = tdrs_id in orbit_screen.active_tdrs
            print(f"TDRS{tdrs_id}: {'ACTIVE' if is_active else 'inactive'}")
        
        print("✓ Orbit screen active TDRS functionality works!")
        
    except Exception as e:
        print(f"✗ Error testing orbit screen: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    create_real_tdrs_data()
    time.sleep(1)  # Give database time to update
    test_orbit_screen_active_tdrs() 