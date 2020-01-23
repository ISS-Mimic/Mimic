import matplotlib as mpl
import matplotlib.pyplot as plt
import datetime as dt
from mpl_toolkits.basemap import Basemap
from matplotlib import path
import numpy as np
from datetime import datetime, timedelta #used for time conversions and logging timestamps

#this code uses basemap to draw the earth map and add the night section to the map
#shamelessly stole most of this from stack overflow 

def bluemarble_daynight(date,scale):
    mpl.rcParams['savefig.pad_inches'] = 0
    # Define Bluemarble and Nightshade objects
    #fig, axes = plt.subplots(1, figsize=(12,8), frameon=False)
    fig = plt.figure(figsize=(12,8))
    axes = plt.axes([0,0,1,1], frameon=False)
    axes.get_xaxis().set_visible(False)
    axes.get_yaxis().set_visible(False)
    plt.autoscale(tight=True)
    m  = Basemap(projection='cyl', resolution= None,
                 area_thresh=None, ax=axes)
    bm = m.bluemarble(scale=scale)
    ns = m.nightshade(date, alpha=0.5)

    bm_rgb = bm.get_array()
    bm_ext = bm.get_extent()

    axes.cla()

    # Get the x and y index spacing
    x = np.linspace(bm_ext[0], bm_ext[1], bm_rgb.shape[1])
    y = np.linspace(bm_ext[2], bm_ext[3], bm_rgb.shape[0])

    # Define coordinates of the Bluemarble image
    x3d,y3d = np.meshgrid(x,y)
    pts     = np.hstack((x3d.flatten()[:,np.newaxis],y3d.flatten()[:,np.newaxis]))

    # Find which coordinates fall in Nightshade 
    # The following could be tidied up as there should only ever one polygon. Although
    # the length of ns.collections is 3? I'm sure there's a better way to do this.
    paths, polygons = [], []
    for i, polygons in enumerate(ns.collections):
        for j, paths in enumerate(polygons.get_paths()):
            #print j, i
            msk = paths.contains_points(pts)

    # Redefine mask
    msk        = np.reshape(msk,bm_rgb[:,:,0].shape)
    msk_s      = np.zeros(msk.shape)
    msk_s[~msk] = 1.

    # Smooth interface between Night and Day
    for s in range(bm_rgb.shape[1]//50): # Make smoothing between day and night a function of Bluemarble resolution
        msk_s = 0.25 * (  np.vstack( (msk_s[-1,:            ], msk_s[:-1, :            ]) )  \
                        + np.vstack( (msk_s[1:,:            ], msk_s[0  , :            ]) )  \
                        + np.hstack( (msk_s[: ,0, np.newaxis], msk_s[:  , :-1          ]) )  \
                        + np.hstack( (msk_s[: ,1:           ], msk_s[:  , -1,np.newaxis]) ) )

    # Define new RGBA array
    bm_rgba = np.dstack((bm_rgb, msk_s))

    # Plot up Bluemarble Nightshade
    m    = Basemap(projection='cyl', resolution= None, 
                   area_thresh=None, ax=axes)
    bm_n = m.warpimage('/home/pi/Mimic/Pi/imgs/orbit/earth_lights_lrg.jpg',scale=scale)
    bm_d = m.imshow(bm_rgba)
    plt.savefig('/home/pi/Mimic/Pi/imgs/orbit/map.jpg', bbox_inches='tight', pad_inches=0)

date = datetime.utcnow()
bluemarble_daynight(date,0.3)
