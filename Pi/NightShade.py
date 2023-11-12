import datetime
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from cartopy.feature.nightshade import Nightshade
from pathlib import Path

home_dir = Path.home()
mimic_data_path = home_dir / '.mimic_data'

fig = plt.figure(figsize=(10, 5))
ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
date = datetime.datetime.utcnow()
ax.stock_img()
ax.add_feature(Nightshade(date, alpha=0.2))
plt.savefig(mimic_data_path / 'map.jpg', bbox_inches='tight', pad_inches=0)
