import numpy as np
import os
import matplotlib.pyplot as plt
import ephem
import json
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import os.path as op
from pathlib import Path
from utils.logger import log_info, log_error

mimic_data_path = Path.home() / '.mimic_data'
temp_image_path = mimic_data_path / 'globe_tmp.png'
final_image_path = mimic_data_path / 'globe.png'

# Assuming the __file__ is defined in your context
mimic_directory = op.abspath(op.join(__file__, op.pardir, op.pardir, op.pardir))

log_info("Running Orbit Globe.")


iss_config_filename = mimic_data_path / 'iss_tle_config.json'
try:
    #log_info(f"Loading ISS TLE data from: {iss_config_filename}")
    with open(iss_config_filename, 'r') as file:
        config = json.load(file)
        ISS_TLE_Line1 = config['ISS_TLE_Line1']
        ISS_TLE_Line2 = config['ISS_TLE_Line2']
    #log_info("Successfully loaded ISS TLE data from config file")
    
except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
    log_error(f"Failed to load ISS TLE data: {e}")
    raise
else:
    #log_info("Creating ISS satellite object from TLE data")
    iss = ephem.readtle("ISS (ZARYA)", ISS_TLE_Line1, ISS_TLE_Line2)

    #log_info("Computing current ISS position")
    iss.compute()
    latitude = np.rad2deg(iss.sublat)
    longitude = np.rad2deg(iss.sublong)
    #log_info(f"Current ISS position: Lat {latitude:.2f}°, Lon {longitude:.2f}°")

    #log_info("Calculating ISS orbit groundtrack (95 minutes)")
    orbit_lat = []
    orbit_lon = []
    for t in range(95):
        iss.compute(ephem.now() + t * ephem.minute)
        orbit_lat.append(np.rad2deg(iss.sublat))
        orbit_lon.append(np.rad2deg(iss.sublong))
    #log_info(f"Calculated {len(orbit_lat)} orbit points")


def plot_earth_no_color():
    try:
        #log_info("Starting Earth globe image generation")
        fig = plt.figure(figsize=(6, 6))
        ax = fig.add_subplot(1, 1, 1, projection=ccrs.Orthographic(longitude, latitude))

        ax.set_global()  # This should set the map to a global view within the projection's limits

        #log_info("Adding map features (ocean, land, coastline, borders)")
        ax.add_feature(cfeature.OCEAN)
        ax.add_feature(cfeature.LAND)
        ax.add_feature(cfeature.COASTLINE)
        ax.add_feature(cfeature.BORDERS, linestyle=':')

        # Plot the groundtrack of the ISS
        #log_info("Plotting ISS orbit groundtrack")
        ax.plot(orbit_lon, orbit_lat, color='green', linewidth=4, transform=ccrs.Geodetic())

        # Plot the current location of the ISS
        #log_info("Plotting current ISS position")
        ax.plot(longitude, latitude, 'ro', markersize=15, transform=ccrs.Geodetic())

        # Writing file to temp path and then changing name to
        # hopefully avoid conflicts in GUI reading image
        #log_info(f"Saving image to temporary path: {temp_image_path}")
        plt.savefig(temp_image_path, dpi=100, transparent=True)
        #plt.savefig(final_image_path, dpi=100, transparent=True)

        # Ensure the file is fully written to disk
        try:
            #log_info("Ensuring image file is fully written to disk")
            with open(temp_image_path, 'rb+') as f:
                f.flush()
                os.fsync(f.fileno())
            #log_info("Image file successfully written to disk")
        except Exception as e:
            log_error(f"Error ensuring image file is written to disk: {e}")
            raise

        # Atomically rename the temporary file to the final filename
        #log_info(f"Moving temporary image to final path: {final_image_path}")
        os.replace(temp_image_path, final_image_path)
        #log_info("Earth globe image generation completed successfully")
        
    except Exception as e:
        log_error(f"Error generating Earth globe image: {e}")
        raise

def main():
    """Main function to generate the Earth globe image with error handling."""
    try:
        log_info("Starting orbit globe generation process")
        plot_earth_no_color()
        #log_info("Orbit globe generation process completed successfully")
        
    except Exception as e:
        log_error(f"Orbit globe generation failed: {e}")
        raise

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log_error(f"Fatal error during orbit globe generation: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
else:
    # When imported as a module, just call the function
    main()
