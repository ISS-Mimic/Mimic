import json
from datetime import datetime, timedelta
import requests  # This will be needed for the HTTP request to Celestrak


def fetch_tdrs_tles_from_celestrak(url):
    # This is a placeholder for the function that fetches the TLEs for TDRS satellites.
    # You will need to replace this with your code that makes an HTTP request to Celestrak.
    response = requests.get(url)
    if response.status_code == 200:
        lines = response.text.strip().split('\n')
        tdrs_tles = {}
        for i in range(0, len(lines), 3):
            if "TDRS" in lines[i]:
                satellite_name = lines[i].strip()
                tdrs_tles[satellite_name] = (lines[i + 1].strip(), lines[i + 2].strip())
        return tdrs_tles
    else:
        response.raise_for_status()


def getTLE_TDRS():
    config_filename = '/dev/shm/tdrs_tle_config.json'  # Update the path as necessary
    tdrs_tle_url = 'https://celestrak.com/NORAD/elements/tdrss.txt'

    # Check if the config file exists and has a valid timestamp
    try:
        with open(config_filename, 'r') as file:
            config = json.load(file)
        last_acquired = datetime.strptime(config['timestamp'], '%Y-%m-%dT%H:%M:%S.%f')
        if datetime.now() - last_acquired < timedelta(days=1):
            # Use the TLEs from the config file if they're less than a day old
            return config['TDRS_TLEs']
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        # If any error occurs, we assume we need to fetch new TLEs
        pass

    # Fetch new TLEs for TDRS satellites from Celestrak
    try:
        tdrs_tles = fetch_tdrs_tles_from_celestrak(tdrs_tle_url)
    except Exception as e:
        # Handle any exceptions during the TLE fetch here
        # You might want to log this error and handle it accordingly
        raise Exception(f"Error fetching TDRS TLEs from Celestrak: {e}")

    # Save the new TLEs and timestamp to the JSON config file
    config = {
        'TDRS_TLEs': tdrs_tles,
        'timestamp': datetime.now().isoformat()
    }
    with open(config_filename, 'w') as file:
        json.dump(config, file)

    return tdrs_tles

#print(getTLE_TDRS())
getTLE_TDRS()

