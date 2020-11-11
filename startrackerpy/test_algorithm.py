#!/usr/bin/env python3
import cv2
import time
import os
from server.startracker.catalog import Catalog
from server.startracker.image import ImageUtils

assets_dir = "/home/igarcia/Nextcloud/University/TFG/reports/assets"
catalogs_path = "./server/startracker/catalogs/out"
catalog = Catalog(f"{catalogs_path}/hip_2000.csv",
                    f"{catalogs_path}/guide_stars_2000_5.csv",
                    f"{catalogs_path}/guide_stars_2000_5_labels.csv")

images_path = "./server/startracker/test_images/ballon"

total = 0
found = 0
not_enough = 0
for filename in os.listdir(images_path):
    print(f"processing image: {filename}")
    image = cv2.imread(f"{images_path}/{filename}")
    gray_img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Noise reduction
    blurred = cv2.GaussianBlur(gray_img, (3, 3), 0)
    threshold = ImageUtils.get_threshold(blurred, 170)
    thresh_image = cv2.threshold(blurred, threshold, 255, cv2.THRESH_BINARY)[1]
    stars = ImageUtils.get_image_stars(thresh_image, gray_img)
    if len(stars) >= 4:
        pattern = catalog.find_stars_pattern(stars[0:4], err=0.010)
        if len(pattern) > 0:
            found += 1
    else:
        print(f"Not enough stars for: {filename}")
        not_enough += 1

    total += 1

print(f"Analyzed a total of {total} stars")
print(f"Found solution for {found}")
print(f"Not enough stars {not_enough}")
