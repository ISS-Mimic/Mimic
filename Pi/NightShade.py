import datetime
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from cartopy.feature.nightshade import Nightshade

fig = plt.figure(figsize=(10, 5))
ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
date = datetime.datetime.utcnow()
print(date)
ax.stock_img()
ax.add_feature(Nightshade(date, alpha=0.2))
plt.savefig('/dev/shm/map.jpg', bbox_inches='tight', pad_inches=0)
