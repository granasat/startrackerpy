#!/usr/bin/env python3
import cv2
import imutils
import matplotlib.pyplot as plt
from scipy.stats import norm
import numpy as np
from image_star import ImageStar
from catalog import Catalog

def compute_i_border(cX, cY, ROI, gray):
    offset = int((ROI-1)/2)
    x_start = cX - offset # 0
    x_end = cX + offset # 4
    y_start = cY - offset # 0
    y_end = cY + offset # 4
    i_border = 0

    if x_start < 0 or x_end >= gray.shape[1]:
        return i_border
    if y_start < 0 or y_end >= gray.shape[0]:
        return i_border

    for x in range(x_start, x_end+1):
        i_border += gray[y_start][x] # Top border
        i_border += gray[y_end][x] # Bottom border

    for y in range(y_start+1, y_end):
        i_border += gray[y][x_start] # Left border
        i_border += gray[y][x_end] # Right border

    return i_border/(4*(ROI-1))


def compute_i_brightness(cX, cY, i_border, gray):
    offset = int((ROI-1) / 2 - 1)
    x_start = cX - offset
    x_end = cX + offset
    y_start = cY - offset
    y_end = cY + offset
    i_brightness = 0

    if x_start < 0 or x_end > gray.shape[1]:
        return i_brightness
    if y_start < 0 or y_end > gray.shape[0]:
        return i_brightness

    for x in range(x_start, x_end+1):
        for y in range(y_start, y_end+1):
            pixel_value = gray[y][x]
            i_brightness += i_brightness + (pixel_value-i_border)

    return i_brightness



def unitary_vector(centroid, pp, f):
    c = pp/f
    x = centroid[0]
    y = centroid[1]

    x_u = x*c*(1+(x**2+y**2)*(c**2))**(-0.5)
    y_u = y*c*(1+(x**2+y**2)*(c**2))**(-0.5)
    z_u = (1+(x**2+y**2)*(c**2))**(-0.5)

    return [x_u, y_u, z_u]



# Constants
pp = 4.65*10**(-3)
f = 12


plt.figure(figsize=(12, 10))
assets_dir = "/home/igarcia/Nextcloud/University/TFG/reports/assets"
# image = cv2.imread("./test_images/polar_05sec.jpg")
# image = cv2.imread("./test_images/polar_30sec.jpg")
image = cv2.imread("./test_images/vega_05sec.jpg")
image2 = cv2.imread("./test_images/polar_05sec.jpg")


# Define ROI, must be odd number
ROI = 9

# Grayscale
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
# Noise reduction
blurred = cv2.GaussianBlur(gray, (3, 3), 0)

# normal distribution and standard deviation
mean, std=norm.fit(blurred)
# Threshold min value
thresh_min_value = int(mean + 3.6 * std)

# Apply threshold
thresh = cv2.threshold(blurred, thresh_min_value, 255, cv2.THRESH_BINARY)[1]
# Find contours
cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                        cv2.CHAIN_APPROX_SIMPLE)

stars = []
# Get the contours found
cnts = imutils.grab_contours(cnts)
# Draw the contours
for c in cnts:
    M = cv2.moments(c)
    # Area of contour
    area = M["m00"]
    # Discard contours with less than 1 pixel area
    if area < 2.0:
        continue
    # Centroid
    cX = int(M["m10"] / M["m00"])
    cY = int(M["m01"] / M["m00"])

    # Compute i_border
    i_border = compute_i_border(cX, cY, ROI, gray)
    i_brightness = compute_i_brightness(cX, cY, ROI, gray)

    # Perimeter
    perimeter = cv2.arcLength(c, True)
    # Polygon
    epsilon = 0.002 * area
    approx = cv2.approxPolyDP(c, epsilon, True)
    # Create blank image
    blank_image = np.zeros(gray.shape, np.uint8)

    # draw the contour and fill the area
    cv2.drawContours(blank_image, [approx], -1, (255, 255, 255), -1)
    # Create a mask to select pixels inside the figure
    mask_contour = blank_image == 255
    # Calculate the intensity from the grayscale image
    # filtering out the pixels where in the blank_image their value is not 255
    intensity = np.mean(gray[mask_contour])
    intensity_text = f'{intensity:.2f}'

    star = ImageStar((cX, cY), i_brightness, perimeter, area)
    stars.append(star)

    cv2.putText(image, f'{intensity:.2f}', (cX + 1, cY + 1),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

# Sort stars by brightness
stars = sorted(stars, key=lambda x: x.brightness, reverse=True)
print(f'{len(stars)=}')
star1 = stars[0]
star2 = stars[1]
star3 = stars[2]

print(star1.centroid)
print(star2.centroid)
print(star3.centroid)

# Get unitary vectors
u_v1 = unitary_vector(star1.centroid, pp, f)
u_v2 = unitary_vector(star2.centroid, pp, f)
u_v3 = unitary_vector(star3.centroid, pp, f)

# Get vectors between them
v1 = np.subtract(u_v2, u_v1)
v2 = np.subtract(u_v3, u_v1)
v3 = np.subtract(u_v3, u_v2)

# Get angles
angle1 = np.dot(v1, v2)/(np.linalg.norm(v1)*np.linalg.norm(v2))
angle2 = np.dot(-v1, v3)/(np.linalg.norm(v1)*np.linalg.norm(v3))
angle3 = np.dot(-v2, -v3) / (np.linalg.norm(v2) * np.linalg.norm(v3))
triad_mine = [angle1, angle2, angle3]
triad = [-0.3083, 0.3274, 0.9998]

print("Angles of the triangle's image:", triad_mine)
print("Angles of the triangle's image andres:", triad)

catalog = Catalog("./generation/out/hip_2020.csv",
                  "./generation/out/guide_stars_2020_6.csv",
                  "./generation/out/guide_stars_neighboors_6.json")

candidates = catalog.find_Knn(triad, 100)

for candidate in candidates:
    print(f"found triad candidate: {catalog._fov_catalog[candidate][2]}")
    print(f" HIP_number: {catalog._fov_catalog[candidate][0].hip_number}")

cv2.line(image, star1.centroid, star2.centroid, (255, 0, 0), 1)
cv2.line(image, star2.centroid, star3.centroid, (255, 0, 0), 1)
cv2.line(image, star3.centroid, star1.centroid, (255, 0, 0), 1)

cv2.imshow('Image', image)
cv2.waitKey(0)
cv2.waitKey(0)
