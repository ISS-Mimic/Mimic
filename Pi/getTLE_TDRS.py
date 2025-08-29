import json
from datetime import datetime, timedelta
import requests  # This will be needed for the HTTP request to Celestrak
from pathlib import Path
from utils.logger import log_info, log_error

home_dir = Path.home()
mimic_data_path = home_dir / '.mimic_data'

def fetch_tdrs_tles_from_celestrak(url):
    """Fetch TDRS TLE data from Celestrak website."""
    try:
        log_info(f"Fetching TDRS TLE data from: {url}")
        response = requests.get(url, timeout=30)  # Add timeout for safety
        
        if response.status_code == 200:
            log_info("Successfully received response from Celestrak")
            lines = response.text.strip().split('\n')
            log_info(f"Processing {len(lines)} lines from response")
            
            tdrs_tles = {}
            for i in range(0, len(lines), 3):
                if "TDRS" in lines[i]:
                    satellite_name = lines[i].strip()
                    tdrs_tles[satellite_name] = (lines[i + 1].strip(), lines[i + 2].strip())
                    log_info(f"Found TDRS satellite: {satellite_name}")
            
            if tdrs_tles:
                log_info(f"Successfully found {len(tdrs_tles)} TDRS satellites")
                return tdrs_tles
            else:
                log_error("No TDRS satellites found in response")
                raise ValueError("No TDRS satellites found in response")
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
        log_error(f"Unexpected error fetching TDRS TLEs from Celestrak: {e}")
        raise

def getTLE_TDRS():
    """Get TDRS TLE data, either from cache or by fetching from Celestrak."""
    config_filename = mimic_data_path / 'tdrs_tle_config.json'
    tdrs_tle_url = 'https://celestrak.com/NORAD/elements/tdrss.txt'
    
    log_info("Starting TDRS TLE retrieval process")
    log_info(f"Config file path: {config_filename}")
    log_info(f"TLE source URL: {tdrs_tle_url}")

    # Check if the config file exists and has a valid timestamp
    try:
        if config_filename.exists():
            log_info("Config file found, checking timestamp")
            with open(config_filename, 'r') as file:
                config = json.load(file)
            
            last_acquired = datetime.strptime(config['timestamp'], '%Y-%m-%dT%H:%M:%S.%f')
            age = datetime.now() - last_acquired
            
            log_info(f"Last TLEs acquired: {last_acquired}")
            log_info(f"TLE age: {age}")
            
            if age < timedelta(days=1):
                log_info("Using cached TDRS TLEs (less than 1 day old)")
                log_info(f"Found {len(config['TDRS_TLEs'])} cached TDRS satellites")
                return config['TDRS_TLEs']
            else:
                log_info("Cached TLEs are too old, will fetch new data")
        else:
            log_info("Config file not found, will fetch new TLE data")
            
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        log_error(f"Error reading config file: {e}")
        log_info("Will fetch new TLE data due to config file error")
    except Exception as e:
        log_error(f"Unexpected error reading config file: {e}")
        log_info("Will fetch new TLE data due to unexpected error")

    # Fetch new TLEs for TDRS satellites from Celestrak
    try:
        log_info("Fetching new TDRS TLE data from Celestrak")
        tdrs_tles = fetch_tdrs_tles_from_celestrak(tdrs_tle_url)
        log_info("Successfully fetched new TDRS TLE data")
        
        # Validate TLE data
        if not tdrs_tles:
            raise ValueError("Received empty TDRS TLE data")
        
        # Log summary of found satellites
        for satellite, (line1, line2) in tdrs_tles.items():
            log_info(f"TDRS {satellite}: {line1[:20]}... | {line2[:20]}...")
        
    except Exception as e:
        log_error(f"Error fetching TDRS TLEs from Celestrak: {e}")
        raise

    # Save the new TLEs and timestamp to the JSON config file
    try:
        log_info("Saving new TDRS TLE data to config file")
        
        # Ensure the directory exists
        config_filename.parent.mkdir(parents=True, exist_ok=True)
        
        config = {
            'TDRS_TLEs': tdrs_tles,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(config_filename, 'w') as file:
            json.dump(config, file, indent=2)
        
        log_info("Successfully saved TDRS TLE data to config file")
        
    except Exception as e:
        log_error(f"Error saving TDRS TLE data to config file: {e}")
        # Don't raise here, we still have the TLE data to return
        # But log the error for debugging

    log_info("TDRS TLE retrieval process completed successfully")
    return tdrs_tles

if __name__ == "__main__":
    try:
        log_info("Starting TDRS TLE script")
        result = getTLE_TDRS()
        log_info("TDRS TLE script completed successfully")
        log_info(f"Retrieved TLE data for {len(result)} TDRS satellites")
        for satellite in result.keys():
            log_info(f"  - {satellite}")
    except Exception as e:
        log_error(f"TDRS TLE script failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

