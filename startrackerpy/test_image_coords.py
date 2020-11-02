#!/usr/bin/env python3
import cv2
import numpy as np
import random
from astropy.coordinates import SkyCoord
from astropy import units as u
from server.startracker.catalog import Catalog
from server.startracker.image import ImageUtils

# load catalogs
catalog = Catalog("./server/startracker/catalogs/out/hip2_2000.csv",
                  "./server/startracker/catalogs/out/guide_stars2_2000_5.csv",
                  "./server/startracker/catalogs/out/guide_stars2_2000_5_labels.csv")

image = np.zeros((960, 1280), np.uint8)

catalog_stars = []
sky_stars = []

for i in range(0,100):
    rnd_star = random.randint(1, len(catalog._hip_catalog))
    print(f"Adding catalog star {rnd_star}: ")
    catalog_star = catalog.get_star_by_id(rnd_star)
    if catalog_star.ra is None:
        continue
    catalog_stars.append(catalog_star)
    sky_star = SkyCoord(ra=catalog_star.ra,
                      dec=catalog_star.dec,
                      unit=u.deg)
    sky_stars.append(sky_star)
    catalog_cart = catalog_star.get_cartesian_coords()
    sky_cart = sky_star.cartesian
    print(f"{sky_cart=} {catalog_cart=}")

sky_d = sky_stars[0].separation(sky_stars[50])
catalog_d = catalog_stars[0].get_distance(catalog_stars[50])

print(f"{sky_d=} {catalog_d=}")
