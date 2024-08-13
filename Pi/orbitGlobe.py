import numpy as np
import os
import matplotlib.pyplot as plt
import ephem
import json
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import os.path as op
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler

mimic_data_path = Path.home() / '.mimic_data'
temp_image_path = mimic_data_path / 'globe_tmp.png'
final_image_path = mimic_data_path / 'globe.png'

# Assuming the __file__ is defined in your context
mimic_directory = op.abspath(op.join(__file__, op.pardir, op.pardir, op.pardir))

# Set up basic configuration for the logging system
log_file_path = mimic_directory + '/Mimic/Pi/Logs/mimiclog_orbitGlobe.log'

logger = logging.getLogger('MyLogger')
logger.setLevel(logging.INFO)  # Set logger to INFO level

# Create handler
handler = RotatingFileHandler(log_file_path, maxBytes=1048576, backupCount=5)
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
handler.setLevel(logging.INFO)  # Set handler to INFO level

# Add handler to logger
if not logger.hasHandlers():
    logger.addHandler(handler)

logger.info("Running Orbit Globe.")

def log_info(message):
    logger.info(message)

def log_error(message):
    logger.error(message)


iss_config_filename = mimic_data_path / 'iss_tle_config.json'
try:
    with open(iss_config_filename, 'r') as file:
        config = json.load(file)
        ISS_TLE_Line1 = config['ISS_TLE_Line1']
        ISS_TLE_Line2 = config['ISS_TLE_Line2']
except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
    print(e)
else:
    iss = ephem.readtle("ISS (ZARYA)", ISS_TLE_Line1, ISS_TLE_Line2)

    iss.compute()
    latitude = np.rad2deg(iss.sublat)
    longitude = np.rad2deg(iss.sublong)

    orbit_lat = []
    orbit_lon = []
    for t in range(95):
        iss.compute(ephem.now() + t * ephem.minute)
        orbit_lat.append(np.rad2deg(iss.sublat))
        orbit_lon.append(np.rad2deg(iss.sublong))


def plot_earth_no_color():
    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.Orthographic(longitude, latitude))

    ax.set_global()  # This should set the map to a global view within the projection's limits

    ax.add_feature(cfeature.OCEAN)
    ax.add_feature(cfeature.LAND)
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS, linestyle=':')

    # Plot the groundtrack of the ISS
    ax.plot(orbit_lon, orbit_lat, color='green', linewidth=4, transform=ccrs.Geodetic())

    # Plot the current location of the ISS
    ax.plot(longitude, latitude, 'ro', markersize=15, transform=ccrs.Geodetic())

    #plt.savefig(temp_image_path, dpi=100, transparent=True)
    plt.savefig(final_image_path, dpi=100, transparent=True)

    # Ensure the file is fully written to disk
    #try:
    #    with open(temp_image_path, 'rb+') as f:
    #        f.flush()
    #        os.fsync(f.fileno())
    #except Exception as e:
    #    log_error(e)

    # Atomically rename the temporary file to the final filename
    #os.replace(temp_image_path, final_image_path)

plot_earth_no_color()
