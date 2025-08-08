#!/usr/bin/python

# Test active TDRS functionality with simulated data
import sqlite3
from pathlib import Path

def create_test_tdrs_database():
    """Create a test TDRS database with simulated active TDRS data."""
    print("Creating test TDRS database:")
    
    # Create the database directory if it doesn't exist
    db_dir = Path.home() / ".mimic_data"
    db_dir.mkdir(exist_ok=True)
    
    # Use Pi path for database
    tdrs_db_path = Path("/dev/shm/tdrs.db")
    # Fallback to Windows path if Pi path doesn't exist
    if not tdrs_db_path.parent.exists():
        tdrs_db_path = db_dir / "tdrs.db"
    
    # Create the database
    conn = sqlite3.connect(str(tdrs_db_path))
    cursor = conn.cursor()
    
    # Create the table
    cursor.execute("CREATE TABLE IF NOT EXISTS tdrs (TDRS1 TEXT, TDRS2 TEXT, Timestamp TEXT)")
    
    # Insert test data - simulate TDRS 6 and 11 as active
    cursor.execute("INSERT OR REPLACE INTO tdrs VALUES(?, ?, ?)", ('6', '11', '2024-01-01 12:00:00'))
    
    conn.commit()
    conn.close()
    
    print(f"Test database created at: {tdrs_db_path}")
    print("Active TDRS: TDRS6, TDRS11")

def test_active_tdrs_reading():
    """Test reading active TDRS from database."""
    print("\nTesting active TDRS reading:")
    
    # Try Pi path first, then Windows path
    tdrs_db_path = Path("/dev/shm/tdrs.db")
    if not tdrs_db_path.exists():
        tdrs_db_path = Path.home() / ".mimic_data" / "tdrs.db"
    
    if tdrs_db_path.exists():
        try:
            conn = sqlite3.connect(str(tdrs_db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT TDRS1, TDRS2, Timestamp FROM tdrs LIMIT 1")
            result = cursor.fetchone()
            conn.close()
            
            if result:
                active_tdrs = [int(result[0]) if result[0] != '0' else 0, 
                              int(result[1]) if result[1] != '0' else 0]
                print(f"Active TDRS: {active_tdrs}")
                print(f"Timestamp: {result[2]}")
                
                # Test which TDRS should show circles
                tdrs_ids = [6, 7, 8, 10, 11, 12]
                for tdrs_id in tdrs_ids:
                    is_active = tdrs_id in active_tdrs
                    print(f"TDRS{tdrs_id}: {'ACTIVE' if is_active else 'inactive'}")
                    
            else:
                print("No data found in TDRS database")
                
        except Exception as e:
            print(f"Error reading TDRS database: {e}")
    else:
        print("TDRS database not found")
    
    print("Active TDRS reading test completed!")

if __name__ == '__main__':
    create_test_tdrs_database()
    test_active_tdrs_reading() 