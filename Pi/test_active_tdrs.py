#!/usr/bin/python

# Test active TDRS functionality
import sqlite3
from pathlib import Path

def test_tdrs_database():
    """Test TDRS database functionality."""
    print("Testing TDRS database functionality:")
    
    # Check if database exists (try Pi path first, then Windows path)
    tdrs_db_path = Path("/dev/shm/tdrs.db")
    if not tdrs_db_path.exists():
        tdrs_db_path = Path.home() / ".mimic_data" / "tdrs.db"
    print(f"TDRS database path: {tdrs_db_path}")
    print(f"Database exists: {tdrs_db_path.exists()}")
    
    if tdrs_db_path.exists():
        try:
            conn = sqlite3.connect(str(tdrs_db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT TDRS1, TDRS2, Timestamp FROM tdrs LIMIT 1")
            result = cursor.fetchone()
            conn.close()
            
            if result:
                print(f"Active TDRS: TDRS1={result[0]}, TDRS2={result[1]}")
                print(f"Timestamp: {result[2]}")
            else:
                print("No data found in TDRS database")
                
        except Exception as e:
            print(f"Error reading TDRS database: {e}")
    else:
        print("TDRS database not found - will be created when TDRScheck.py runs")
    
    print("Active TDRS test completed!")

if __name__ == '__main__':
    test_tdrs_database() 