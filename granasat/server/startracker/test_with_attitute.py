#!/usr/bin/env python3
import cv2
import imutils
import sys
import matplotlib.pyplot as plt
from scipy.stats import norm
import numpy as np
from image_star import ImageStar
from catalog import Catalog
from math import cos, atan, atan2, sin, sqrt, pi


class Centroid:
    def __init__(self, x, y, brightness):
        self.x = x
        self.y = y
        self.brightness = brightness

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


def unitary_vector(centroid, pp, f):
    c = pp/f
    x = centroid[0]
    y = centroid[1]

    x_u = x*c*(1+(x**2+y**2)*(c**2))**(-0.5)
    y_u = y*c*(1+(x**2+y**2)*(c**2))**(-0.5)
    z_u = (1+(x**2+y**2)*(c**2))**(-0.5)

    return [x_u, y_u, z_u]


def simplify_centroids(centroids, thresh1=9, thresh2=4):
    simplified = []

    for i in range(0, len(centroids)):
        suma_x = 0
        suma_y = 0
        suma_B = 0
        if centroids[i].x != 2000 and centroids[i] != 2000:
            new_x = centroids[i].x
            new_y = centroids[i].y
            new_B = centroids[i].brightness
            pixels = 1

            suma_x = new_x
            suma_y = new_y
            suma_B = new_B

            for j in range(i+1, len(centroids)):
                if abs(new_x - centroids[j].x) <= thresh1 and abs(new_y - centroids[j].y) <= thresh1:
                    suma_x += centroids[j].x
                    suma_y += centroids[j].y
                    suma_B += centroids[j].brightness
                    pixels += 1
                    centroids[j].x = 2000
                    centroids[j].y = 2000

            centroids[i].x = 2000
            centroids[i].y = 2000
            if pixels > thresh2:
                centroid = Centroid(suma_x/pixels, suma_y/pixels, suma_B/pixels)
                simplified.append(centroid)

    return simplified


def computeUnitaryVector(centroid, f):
    CENTER_X = 640
    CENTER_Y = 480
    x = centroid.x - CENTER_X
    y = centroid.y - CENTER_Y
    x_u = cos(atan2(y, x)) * cos(pi/2 - atan(sqrt(pow(x/f, 2)+pow(y/f, 2))))
    y_u = sin(atan2(y, x)) * cos(pi/2 - atan(sqrt(pow(x/f, 2)+pow(y/f, 2))))
    z_u = sin(pi/2 - atan(sqrt(pow(x/f, 2) + pow(y/f, 2))))

    return [x_u, y_u, z_u]


def find_star_pattern(vector, stars_used, err, catalog, k_vector, stars, real_vector):
    """
    vector: is a list of possible stars (unitary vectors of centroids)
    """
    unitaries = []
    # Step 1 add the first 3 from vector to unitaries
    # could be unitaries = vector[0:3]
    for i in range(0, 3):
        unitaries.append(vector[i])

    # Step 2 create trios from vector
    create_trios(vector, 3, umb, )
    pass

# Constants
pp = 4.65*10**(-3)
f = 12
FOCAL_LENGTH = 2657


plt.figure(figsize=(12, 10))
assets_dir = "/home/igarcia/Nextcloud/University/TFG/reports/assets"
# image = cv2.imread("./test_images/polar_05sec.jpg")
image = cv2.imread("./test_images/vega_05sec.jpg")
image2 = cv2.imread("./test_images/polar_05sec.jpg")


# Define ROI, must be odd number
my_ROI = 9

# Grayscale
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
thresh_min_value = 80

centroids = []
# Get the contours found
limit = int((my_ROI-1)/2)
for x in range(limit, gray.shape[1]-limit):
    for y in range(limit, gray.shape[0]-limit):
        if gray[y][x] >= thresh_min_value:
            my_i_border = compute_i_border(x, y, my_ROI, gray)
            my_x_cm, my_y_cm, my_B = compute_i_brightness(x, y, my_i_border, my_ROI, gray)
            centroid = Centroid(my_x_cm, my_y_cm, my_B)
            centroids.append(centroid)


centroids = simplify_centroids(centroids)
# Sort centroids by brightness
centroids = sorted(centroids, key=lambda x: x.brightness, reverse=True)

# Compute unitary vectors
unitaries = []
for centroid in centroids:
    unitaries.append(computeUnitaryVector(centroid, FOCAL_LENGTH))

# load catalogs
catalog = Catalog("./generation/out/hip_2020.csv",
                  "./generation/out/guide_stars_2020_6.csv",
                  "./generation/out/guide_stars_neighboors_6.json")

# vector = find_star_pattern(unitaries, stars_used, err,)

print(f'{len(centroids)=}')
for centroid in centroids:
    print(f'Centroid: [x: {centroid.x}, y: {centroid.y}, brightness: {centroid.brightness}]')

print(f'{len(unitaries)=}')
for unitary in unitaries:
    print(f'Unitary: [x: {unitary[0]}, y: {unitary[1]}, z: {unitary[2]}]')

star1 = centroids[0]
star2 = centroids[1]
star3 = centroids[2]

u_v1 = computeUnitaryVector(centroids[0], FOCAL_LENGTH)
u_v2 = computeUnitaryVector(centroids[1], FOCAL_LENGTH)
u_v3 = computeUnitaryVector(centroids[2], FOCAL_LENGTH)

print(f'{u_v2=} should be {unitaries[1]=}')
# Get vectors between them
v1 = np.subtract(u_v2, u_v1)
v2 = np.subtract(u_v3, u_v1)
v3 = np.subtract(u_v3, u_v2)

# Get angles
angle1 = np.dot(v1, v2)/(np.linalg.norm(v1)*np.linalg.norm(v2))
angle2 = np.dot(-v1, v3)/(np.linalg.norm(v1)*np.linalg.norm(v3))
angle3 = np.dot(-v2, -v3) / (np.linalg.norm(v2) * np.linalg.norm(v3))


triad_mine = [angle1, angle2, angle3]
# triad = [-0.3083, 0.3274, 0.9998] # This is polar05sec in matlab
triad = [-0.9989, 0.9999, 0.9994]

print("Angles of the triangle's image:", triad_mine)
print("Angles of the triangle's image andres:", triad)


candidates = catalog.find_Knn(triad, 5)

for candidate in candidates:
    print(f"found triad candidate: {catalog._fov_catalog[candidate][2]}")
    print(f"  hip_number: {catalog._fov_catalog[candidate][0].hip_number}")

candidates = catalog.find_Knn(triad_mine, 200)

for candidate in candidates:
    print(f"found triad candidate: {catalog._fov_catalog[candidate][2]}")
    print(f"  hip_number: {catalog._fov_catalog[candidate][0].hip_number}")

cv2.line(image, (int(centroids[0].x), int(centroids[0].y)), (int(centroids[1].x), int(centroids[1].y)), (255, 0, 0), 1)
cv2.line(image, (int(centroids[1].x), int(centroids[1].y)), (int(centroids[2].x), int(centroids[2].y)), (255, 0, 0), 1)
cv2.line(image, (int(centroids[2].x), int(centroids[2].y)), (int(centroids[0].x), int(centroids[0].y)), (255, 0, 0), 1)

cv2.imshow('Image', image)
cv2.waitKey(0)
cv2.waitKey(0)
