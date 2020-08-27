#!/usr/bin/env python3
import cv2
import json
import numpy as np
from image_star import ImageStar, Centroid
from catalog import Catalog

def compute_i_border(cX, cY, ROI, img):
    offset = int((ROI-1)/2)
    x_start = cX - offset # 0
    x_end = cX + offset # 4
    y_start = cY - offset # 0
    y_end = cY + offset # 4
    i_border = 0

    if x_start < 0 or x_end >= img.shape[1]:
        return i_border
    if y_start < 0 or y_end >= img.shape[0]:
        return i_border

    for x in range(x_start, x_end+1):
        i_border += img[y_start][x] # Top border
        i_border += img[y_end][x] # Bottom border

    for y in range(y_start+1, y_end):
        i_border += img[y][x_start] # Left border
        i_border += img[y][x_end] # Right border

    return i_border/(4*(ROI-1))


def compute_i_brightness(cX, cY, i_border, ROI, img):
    offset = int((ROI-1) / 2 - 1)
    x_start = cX - offset
    x_end = cX + offset
    y_start = cY - offset
    y_end = cY + offset
    B = 0

    if x_start < 0 or x_end > img.shape[1]:
        return B
    if y_start < 0 or y_end > img.shape[0]:
        return B

    for x in range(x_start, x_end+1):
        for y in range(y_start, y_end+1):
            pixel_value = img[y][x]
            B += pixel_value - i_border
    x_cm = 0.0
    y_cm = 0.0
    if B != 0:
        for x in range(x_start, x_end+1):
            for y in range(y_start, y_end+1):
                pixel_value = img[y][x] - i_border
                x_cm = x_cm + (x*pixel_value)/B
                y_cm = y_cm + (y*pixel_value)/B
    else:
        x_cm = x_start + (x_end-x_start)/2
        y_cm = y_start + (y_end-y_start)/2

    return [x_cm, y_cm, B]


def simplify_img_stars(stars, thresh1=9, thresh2=4):
    simplified = []

    for i in range(0, len(stars)):
        suma_x = 0
        suma_y = 0
        suma_B = 0
        if stars[i].centroid.x != 2000 and stars[i].centroid.y != 2000:
            new_x = stars[i].centroid.x
            new_y = stars[i].centroid.y
            new_B = stars[i].brightness
            pixels = 1

            suma_x = new_x
            suma_y = new_y
            suma_B = new_B

            for j in range(i+1, len(stars)):
                if abs(new_x - stars[j].centroid.x) <= thresh1 and abs(new_y - stars[j].centroid.y) <= thresh1:
                    suma_x += stars[j].centroid.x
                    suma_y += stars[j].centroid.y
                    suma_B += stars[j].brightness
                    pixels += 1
                    stars[j].centroid.x = 2000
                    stars[j].centroid.y = 2000

            stars[i].centroid.x = 2000
            stars[i].centroid.y = 2000
            if pixels > thresh2:
                centroid = Centroid(suma_x/pixels, suma_y/pixels)
                img_star = ImageStar(centroid, suma_B/pixels)
                simplified.append(img_star)

    return simplified


# Constants
pp = 4.65*10**(-3)
f = 12

assets_dir = "/home/igarcia/Nextcloud/University/TFG/reports/assets"
image = cv2.imread("./test_images/vega_05sec.jpg")
# image = cv2.imread("./test_images/polar_30sec.jpg") # 100
# image = cv2.imread("./test_images/polar_05sec.jpg") # 13

# Grayscale
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

img_stars = []
# Step 1: Get possible Image stars, these are possible stars in the image.
# Define ROI, must be odd number
my_ROI = 9
limit = int((my_ROI - 1) / 2)
thresh_min_value = 90
for x in range(limit, gray.shape[1]-limit):
    for y in range(limit, gray.shape[0]-limit):
        if gray[y][x] >= thresh_min_value:
            my_i_border = compute_i_border(x, y, my_ROI, gray)
            my_x_cm, my_y_cm, my_B = compute_i_brightness(x, y, my_i_border, my_ROI, gray)
            centroid = Centroid(my_x_cm, my_y_cm)
            img_star = ImageStar(centroid, my_B)
            img_stars.append(img_star)

img_stars = simplify_img_stars(img_stars)
# Sort image stars by brightness
img_stars = sorted(img_stars, key=lambda x: x.brightness, reverse=True)

# Compute unitary vectors
unitaries = []
for img_star in img_stars:
    unitaries.append(img_star.get_unitary_vector())

# load catalogs
catalog = Catalog("./generation/out/hip_2020.csv",
                  "./generation/out/guide_stars_2020_5.csv",
                  "./generation/out/guide_stars_neighboors_5.json")

print(f'{len(img_stars)=}')
for img_star in img_stars:
    print(f'Centroid: [x: {img_star.centroid.x}, y: {img_star.centroid.y}, brightness: {img_star.brightness}]')

print(f'{len(unitaries)=}')
for unitary in unitaries:
    print(f'Unitary: [x: {unitary[0]}, y: {unitary[1]}, z: {unitary[2]}]')


star1 = img_stars[0]
star2 = img_stars[1]
star3 = img_stars[2]
star4 = img_stars[3]


triplets_triangle1 = catalog.find_star_pattern([star1, star2, star3], threshold=0.1)
print(f'{triplets_triangle1=}')
triplets_triangle2 = catalog.find_star_pattern([star1, star2, star4], threshold=0.1)
print(f'{triplets_triangle2=}')

real_stars = catalog.get_common_stars(triplets_triangle1, triplets_triangle2)
print(f'{real_stars=}')

cv2.line(image, (int(star1.centroid.x), int(star1.centroid.y)), (int(star2.centroid.x), int(star2.centroid.y)), (255, 0, 0), 1)
cv2.line(image, (int(star2.centroid.x), int(star2.centroid.y)), (int(star3.centroid.x), int(star3.centroid.y)), (0, 0, 255), 1)
cv2.line(image, (int(star3.centroid.x), int(star3.centroid.y)), (int(star1.centroid.x), int(star1.centroid.y)), (0, 0, 255), 1)
cv2.line(image, (int(star4.centroid.x), int(star4.centroid.y)), (int(star1.centroid.x), int(star1.centroid.y)), (0, 255, 0), 1)
cv2.line(image, (int(star4.centroid.x), int(star4.centroid.y)), (int(star2.centroid.x), int(star2.centroid.y)), (0, 255, 0), 1)

cv2.imshow('Image', image)
cv2.waitKey(0)
cv2.waitKey(0)
