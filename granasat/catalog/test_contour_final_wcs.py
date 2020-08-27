#!/usr/bin/env python3
# Color: BGR
import argparse
import imutils
import cv2
import sys
import numpy as np
from scipy.signal import argrelextrema
import matplotlib.pyplot as plt
from scipy.stats import norm
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.wcs import WCS
from astropy.wcs.utils import fit_wcs_from_points
from image_star import ImageStar, Centroid
from catalog import Catalog


print("Loading catalog")
# load catalogs
catalog = Catalog("./generation/out/hip_2000.csv",
                  "./generation/out/guide_stars_2000_5.csv",
                  "./generation/out/guide_stars_2000_5_labels.csv")
print("Catalog loaded")

# load the image, convert it to grayscale, blur it slightly,
# and threshold it
# image = cv2.imread("./test_images/vega_05sec.jpg")
# image = cv2.imread("./test_images/polar_05sec.jpg")
image = cv2.imread("./test_images/polar_30sec.jpg")
# image = cv2.imread("./test_images/andromeda 05seg.jpg")
# image = cv2.imread("./test_images/casiopea 01seg gain max.jpg")
# image = cv2.imread("./test_images/test01.jpg")
# image = cv2.imread("./test_images/test_artificial.png")
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
# Noise reduction
blurred = cv2.GaussianBlur(gray, (3, 3), 0)

# Get histogram
hist = cv2.calcHist([blurred], [0], None, [256], [0, 256])
mean, std=norm.fit(blurred)
print(f"{mean=}, {std=}, {mean + 3.6*std=}")
thresh_min_value = int(mean + 3.6*std)
print("Threshold selected:", thresh_min_value)

thresh = cv2.threshold(blurred, thresh_min_value, 255, cv2.THRESH_BINARY)[1]
cv2.imshow("Image", thresh)
cv2.waitKey(0)

# find contours in the thresholded image
cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE)
cnts = imutils.grab_contours(cnts)
print("Possible contours:", len(cnts))

i = 1
invalid = 0
img_stars = []
# loop over the contours
for c in cnts:
    M = cv2.moments(c)
    # print(c)

    # Area of contour
    area = M["m00"]
    # Discard stars with area lesser than 3
    if area < 3:
        invalid += 1
        continue
    # Centroid of contour
    cX = int(M["m10"] / M["m00"])
    cY = int(M["m01"] / M["m00"])

    # Perimeter
    perimeter = cv2.arcLength(c, True)

    # Polygon approximation
    epsilon = 0.01 * perimeter
    approx = cv2.approxPolyDP(c, epsilon, True)

    # Create blank image
    blank_image = np.zeros(gray.shape, np.uint8)
    # Draw contour in the mask
    cv2.drawContours(blank_image, [approx], -1, (255, 255, 255), -1)
    # Create a mask to select pixels inside the figure
    mask_contour = blank_image == 255

    # Calculate the intensity from the grayscale image
    # filtering out the pixels where in the blank_image their value is not 255
    intensity = np.mean(gray[mask_contour])

    img_star = ImageStar(Centroid(cX, cY), intensity, perimeter, area)
    img_stars.append(img_star)
    # draw the contour and center of the shape on the image
    cv2.drawContours(image, [approx], -1, (51, 255, 255), 1)
    # cv2.drawContours(image, [approx], -1, (51, 255, 255), 1)
    #cv2.circle(image, (cX, cY), 3, (255, 255, 255), -1)
    # cv2.putText(image, str(i), (cX + 1, cY + 1),
                # cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # k = cv2.waitKey(0)
    # if k == 113:
    #     sys.exit(0)
    i += 1

    # (x,y),radius = cv2.minEnclosingCircle(c)
    # center = (int(x),int(y))
    # radius = int(radius)
    # cv2.circle(image,center,radius,(0,255,0),1)
    # show the image

# show the plotting graph of an image, uncomment
plt.plot(hist)
plt.show()

print("Stars found:", len(cnts) - invalid)

img_stars = sorted(img_stars, key=lambda x: x.brightness, reverse=True)

# Get the 4 possible stars to do triangles
star1 = img_stars[0]
star2 = img_stars[1]
star3 = img_stars[2]
star4 = img_stars[3]

# Get triplets for the first triangle
triplets_triangle1 = catalog.find_star_pattern([star1, star2, star3], threshold=0.006)
print(f'{triplets_triangle1=}')
# Get triplets for the second triangle
triplets_triangle2 = catalog.find_star_pattern([star1, star3, star4], threshold=0.006)
print(f'{triplets_triangle2=}')
triplets_triangle3 = catalog.find_star_pattern([star1, star2, star4], threshold=0.006)
print(f'{triplets_triangle3=}')

# Get the stars in both triangles.
common, news = catalog.get_common_stars(triplets_triangle1, triplets_triangle2)
print(f'{common=}')
print(f'{news=}')

pixels_x = np.array([])
pixels_y = np.array([])
stars_ra = []
stars_dec = []

# To build the WCS we use only the common stars
for found_star in common:
    center = (found_star.centroid.x, found_star.centroid.y)
    radius = 10
    cv2.circle(image, center, radius, (0, 255, 0), 1)
    center = (found_star.centroid.x - 25, found_star.centroid.y - 25)
    cv2.putText(image, str(found_star.real_star.name), center,
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
    pixels_x = np.append(pixels_x, found_star.centroid.x)
    pixels_y = np.append(pixels_y, found_star.centroid.y)
    stars_ra.append(found_star.real_star.ra)
    stars_dec.append(found_star.real_star.dec)


stars = SkyCoord(ra=stars_ra, dec=stars_dec, unit=u.deg)
my_wcs = fit_wcs_from_points((pixels_x, pixels_y), stars)
print(my_wcs)
print(pixels_x)
print(pixels_y)
print(stars)


img_stars_to_label = []
max_labels = 20
i = 0
for img_star in img_stars:
    if i >= max_labels:
        break
    for found_star in common + news:
        if found_star.centroid == img_star.centroid:
            print("same centroid")
            break
    img_stars_to_label.append(img_star)
    i += 1

# Set wcs coordinates to ImageStars
for img_star in img_stars:
    pixel_x = np.array([[img_star.centroid.x]])
    pixel_y = np.array([[img_star.centroid.y]])
    coords_ra, coords_dec = my_wcs.wcs_pix2world(pixel_x, pixel_y, 0)
    coords = SkyCoord(ra=coords_ra, dec=coords_dec, unit=u.deg)
    img_star.set_wcs_coords(coords)

# Test to match pixels to entries in the catalog
labeled = 0
for hip_number in catalog._guide_stars:
    star = catalog.get_star_by_id(int(hip_number))
    coords_a = SkyCoord(ra=star.ra, dec=star.dec, unit=u.deg)
    for img_star in img_stars_to_label:
        if img_star.is_labeled():
            continue
        coords_b = img_star.get_wcs_coords()
        if coords_a.separation(coords_b) < 0.8 * u.deg:
            center = (img_star.centroid.x - 20, img_star.centroid.y + 25)
            cv2.putText(image, str(star.name), center,
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
            labeled += 1
            img_star.set_labeled()

print(f'Could label: {labeled} guide stars.')


cv2.line(image, (int(star1.centroid.x), int(star1.centroid.y)), (int(star2.centroid.x), int(star2.centroid.y)), (0, 0, 255), 1)
cv2.line(image, (int(star2.centroid.x), int(star2.centroid.y)), (int(star3.centroid.x), int(star3.centroid.y)), (0, 0, 255), 1)
cv2.line(image, (int(star3.centroid.x), int(star3.centroid.y)), (int(star1.centroid.x), int(star1.centroid.y)), (255, 0, 0), 1)
cv2.line(image, (int(star4.centroid.x), int(star4.centroid.y)), (int(star1.centroid.x), int(star1.centroid.y)), (0, 255, 0), 1)
cv2.line(image, (int(star4.centroid.x), int(star4.centroid.y)), (int(star3.centroid.x), int(star3.centroid.y)), (0, 255, 0), 1)

cv2.imshow("Image", image)
while True:
    k = cv2.waitKey(0)
    if k == 113:
        sys.exit(0)
        # 113 -> q
        # 32  -> space
