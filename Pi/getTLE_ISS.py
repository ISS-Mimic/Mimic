import json
from datetime import datetime, timedelta
import requests  # This will be needed for the HTTP request to Celestrak
from pathlib import Path
from utils.logger import log_info, log_error

home_dir = Path.home()
mimic_data_path = home_dir / '.mimic_data'

def fetch_tle_from_celestrak(url):
    """Fetch TLE data from Celestrak website."""
    try:
        log_info(f"Fetching TLE data from: {url}")
        response = requests.get(url, timeout=30)  # Add timeout for safety
        
        if response.status_code == 200:
            log_info("Successfully received response from Celestrak")
            lines = response.text.strip().split('\n')
            log_info(f"Processing {len(lines)} lines from response")
            
            for i in range(0, len(lines), 3):
                if "ISS (ZARYA)" in lines[i]:
                    log_info("Found ISS (ZARYA) TLE data")
                    return lines[i + 1].strip(), lines[i + 2].strip()
            
            log_error("ISS (ZARYA) TLE data not found in response")
            raise ValueError("ISS (ZARYA) TLE data not found in response")
        else:
            log_error(f"HTTP request failed with status code: {response.status_code}")
            response.raise_for_status()
            
    except requests.exceptions.Timeout:
        log_error("Request to Celestrak timed out")
        raise
    except requests.exceptions.RequestException as e:
        log_error(f"Request to Celestrak failed: {e}")
        raise
    except Exception as e:
        log_error(f"Unexpected error fetching TLE from Celestrak: {e}")
        raise

def getTLE_ISS():
    """Get ISS TLE data, either from cache or by fetching from Celestrak."""
    config_filename = mimic_data_path / 'iss_tle_config.json'
    iss_tle_url = 'https://celestrak.com/NORAD/elements/stations.txt'
    
    log_info("Starting ISS TLE retrieval process")
    log_info(f"Config file path: {config_filename}")
    log_info(f"TLE source URL: {iss_tle_url}")

    # Check if the config file exists and has a valid timestamp
    try:
        if config_filename.exists():
            log_info("Config file found, checking timestamp")
            with open(config_filename, 'r') as file:
                config = json.load(file)
            
            last_acquired = datetime.strptime(config['timestamp'], '%Y-%m-%dT%H:%M:%S.%f')
            age = datetime.now() - last_acquired
            
            log_info(f"Last TLE acquired: {last_acquired}")
            log_info(f"TLE age: {age}")
            
            if age < timedelta(days=1):
                log_info("Using cached TLE (less than 1 day old)")
                return config['ISS_TLE_Line1'], config['ISS_TLE_Line2']
            else:
                log_info("Cached TLE is too old, will fetch new data")
        else:
            log_info("Config file not found, will fetch new TLE data")
            
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        log_error(f"Error reading config file: {e}")
        log_info("Will fetch new TLE data due to config file error")
    except Exception as e:
        log_error(f"Unexpected error reading config file: {e}")
        log_info("Will fetch new TLE data due to unexpected error")

    # Fetch a new TLE from Celestrak
    try:
        log_info("Fetching new TLE data from Celestrak")
        ISS_TLE_Line1, ISS_TLE_Line2 = fetch_tle_from_celestrak(iss_tle_url)
        log_info("Successfully fetched new TLE data")
        
        # Validate TLE data
        if not ISS_TLE_Line1 or not ISS_TLE_Line2:
            raise ValueError("Received empty TLE data")
        
        log_info(f"TLE Line 1: {ISS_TLE_Line1[:20]}...")
        log_info(f"TLE Line 2: {ISS_TLE_Line2[:20]}...")
        
    except Exception as e:
        log_error(f"Error fetching TLE from Celestrak: {e}")
        raise

    # Save the new TLE and timestamp to the JSON config file
    try:
        log_info("Saving new TLE data to config file")
        
        # Ensure the directory exists
        config_filename.parent.mkdir(parents=True, exist_ok=True)
        
        config = {
            'ISS_TLE_Line1': ISS_TLE_Line1,
            'ISS_TLE_Line2': ISS_TLE_Line2,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(config_filename, 'w') as file:
            json.dump(config, file, indent=2)
        
        log_info("Successfully saved TLE data to config file")
        
    except Exception as e:
        log_error(f"Error saving TLE data to config file: {e}")
        # Don't raise here, we still have the TLE data to return
        # But log the error for debugging

    log_info("ISS TLE retrieval process completed successfully")
    return ISS_TLE_Line1, ISS_TLE_Line2

if __name__ == "__main__":
    try:
        log_info("Starting ISS TLE script")
        result = getTLE_ISS()
        log_info("ISS TLE script completed successfully")
        log_info(f"Retrieved TLE data: {result[0][:20]}... | {result[1][:20]}...")
    except Exception as e:
        log_error(f"ISS TLE script failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
