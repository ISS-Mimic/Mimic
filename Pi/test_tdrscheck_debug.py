#!/usr/bin/python

# Test TDRScheck.py execution and dependencies
import subprocess
import sys
from pathlib import Path

def test_tdrscheck_dependencies():
    """Test if all required dependencies are available."""
    print("Testing TDRScheck.py dependencies:")
    
    required_modules = ['twisted', 'autobahn', 'six', 'sqlite3']
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✓ {module} - Available")
        except ImportError as e:
            print(f"✗ {module} - Missing: {e}")
    
    print()

def test_tdrscheck_execution():
    """Test TDRScheck.py execution."""
    print("Testing TDRScheck.py execution:")
    
    # Get the path to TDRScheck.py
    tdrscheck_path = Path(__file__).parent / "TDRScheck.py"
    print(f"TDRScheck.py path: {tdrscheck_path}")
    print(f"File exists: {tdrscheck_path.exists()}")
    
    if not tdrscheck_path.exists():
        print("✗ TDRScheck.py not found!")
        return
    
    try:
        # Try to run TDRScheck.py with a timeout
        result = subprocess.run(
            [sys.executable, str(tdrscheck_path)],
            capture_output=True,
            text=True,
            timeout=10  # 10 second timeout
        )
        
        print(f"Return code: {result.returncode}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        
        if result.returncode == 0:
            print("✓ TDRScheck.py executed successfully")
        else:
            print("✗ TDRScheck.py failed to execute")
            
    except subprocess.TimeoutExpired:
        print("✓ TDRScheck.py is running (timeout reached - this is expected)")
    except Exception as e:
        print(f"✗ Error executing TDRScheck.py: {e}")

def test_database_creation():
    """Test if the TDRS database can be created."""
    print("\nTesting TDRS database creation:")
    
    try:
        import sqlite3
        from pathlib import Path
        
        # Try Pi path first
        db_path = Path("/dev/shm/tdrs.db")
        if not db_path.parent.exists():
            print(f"✗ /dev/shm directory doesn't exist (Windows)")
            # Try Windows path
            db_path = Path.home() / ".mimic_data" / "tdrs.db"
            db_path.parent.mkdir(exist_ok=True)
        
        print(f"Database path: {db_path}")
        
        # Create database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Create table
        cursor.execute("CREATE TABLE IF NOT EXISTS tdrs (TDRS1 TEXT, TDRS2 TEXT, Timestamp TEXT)")
        cursor.execute("INSERT OR REPLACE INTO tdrs VALUES(?, ?, ?)", ('0', '0', '0'))
        
        conn.commit()
        conn.close()
        
        print("✓ TDRS database created successfully")
        
    except Exception as e:
        print(f"✗ Failed to create TDRS database: {e}")

if __name__ == '__main__':
    test_tdrscheck_dependencies()
    test_database_creation()
    test_tdrscheck_execution() 