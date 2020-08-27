#!/usr/bin/env python3
# Color: BGR
import argparse
import imutils
import cv2
import sys
import time
import numpy as np
from scipy.signal import argrelextrema
import matplotlib.pyplot as plt
from scipy.stats import norm
from image_star import ImageStar, Centroid
from catalog import Catalog


# load catalogs
catalog = Catalog("./generation/out/hip_2020.csv",
                  "./generation/out/guide_stars_2020_5.csv",
                  "./generation/out/guide_stars_neighboors_5.json")

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

start = time.time()

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

# TODO: show the plotting graph of an image, uncomment
# plt.plot(hist)
# plt.show()


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

# Get the stars in both triangles.
real_stars = catalog.get_common_stars(triplets_triangle1, triplets_triangle2)
print(f'{real_stars=}')
end = time.time()
print(f'Time spent: {end-start}')

for i in range(0,5):
    print(f'x: {img_stars[i].centroid.x} y: {img_stars[i].centroid.y} brightness: {img_stars[i].brightness}')

# Compute unitary vectors
unitaries = []
for img_star in img_stars:
    unitaries.append(img_star.get_unitary_vector())


print(f'{len(img_stars)=}')
for img_star in img_stars[:5]:
    print(f'Centroid: [x: {img_star.centroid.x}, y: {img_star.centroid.y}, brightness: {img_star.brightness}]')

print(f'{len(unitaries)=}')
for unitary in unitaries[:5]:
    print(f'Unitary: [x: {unitary[0]}, y: {unitary[1]}, z: {unitary[2]}]')




for real_star in real_stars:
    center = (real_star.centroid.x, real_star.centroid.y)
    radius = 10
    cv2.circle(image, center, radius, (0, 255, 0), 1)
    center = (real_star.centroid.x - 25, real_star.centroid.y - 25)
    cv2.putText(image, str(real_star.real_star.hip_number), center,
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
    print(f"Label for star {real_star.real_star.hip_number} in [{real_star.centroid.x}, {real_star.centroid.y}]")



cv2.line(image, (int(star1.centroid.x), int(star1.centroid.y)), (int(star2.centroid.x), int(star2.centroid.y)), (255, 0, 0), 1)
cv2.line(image, (int(star2.centroid.x), int(star2.centroid.y)), (int(star3.centroid.x), int(star3.centroid.y)), (0, 0, 255), 1)
cv2.line(image, (int(star3.centroid.x), int(star3.centroid.y)), (int(star1.centroid.x), int(star1.centroid.y)), (0, 0, 255), 1)
cv2.line(image, (int(star4.centroid.x), int(star4.centroid.y)), (int(star1.centroid.x), int(star1.centroid.y)), (0, 255, 0), 1)
cv2.line(image, (int(star4.centroid.x), int(star4.centroid.y)), (int(star2.centroid.x), int(star2.centroid.y)), (0, 255, 0), 1)

cv2.imshow("Image", image)
while True:
    k = cv2.waitKey(0)
    if k == 113:
        sys.exit(0)
        # 113 -> q
        # 32  -> space
