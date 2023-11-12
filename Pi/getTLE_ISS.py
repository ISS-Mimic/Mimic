import json
from datetime import datetime, timedelta
import requests  # This will be needed for the HTTP request to Celestrak
from pathlib import Path

home_dir = Path.home()
mimic_data_path = home_dir / '.mimic_data'


def fetch_tle_from_celestrak(url):
    # This is a placeholder for the function that actually fetches the TLE.
    # You will need to replace this with your code that makes an HTTP request to Celestrak.
    response = requests.get(url)
    if response.status_code == 200:
        lines = response.text.strip().split('\n')
        for i in range(0, len(lines), 3):
            if "ISS (ZARYA)" in lines[i]:
                return lines[i + 1].strip(), lines[i + 2].strip()
    else:
        response.raise_for_status()


def getTLE_ISS():
    config_filename = mimic_data_path / 'iss_tle_config.json'  # Update the path as necessary
    iss_tle_url = 'https://celestrak.com/NORAD/elements/stations.txt'

    # Check if the config file exists and has a valid timestamp
    try:
        with open(config_filename, 'r') as file:
            config = json.load(file)
        last_acquired = datetime.strptime(config['timestamp'], '%Y-%m-%dT%H:%M:%S.%f')
        if datetime.now() - last_acquired < timedelta(days=1):
            # Use the TLE from the config file if it's less than a day old
            return config['ISS_TLE_Line1'], config['ISS_TLE_Line2']
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        # If any error occurs, we assume we need to fetch a new TLE
        pass

    # Fetch a new TLE from Celestrak
    try:
        ISS_TLE_Line1, ISS_TLE_Line2 = fetch_tle_from_celestrak(iss_tle_url)
    except Exception as e:
        # Handle any exceptions during the TLE fetch here
        # You might want to log this error and handle it accordingly
        raise Exception(f"Error fetching TLE from Celestrak: {e}")

    # Save the new TLE and timestamp to the JSON config file
    config = {
        'ISS_TLE_Line1': ISS_TLE_Line1,
        'ISS_TLE_Line2': ISS_TLE_Line2,
        'timestamp': datetime.now().isoformat()
    }
    with open(config_filename, 'w') as file:
        json.dump(config, file)

    return ISS_TLE_Line1, ISS_TLE_Line2

#print(getTLE_ISS())
getTLE_ISS()
