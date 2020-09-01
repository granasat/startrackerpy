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


# load the image, convert it to grayscale, blur it slightly,
# and threshold it
# image = cv2.imread("./test_images/polar_05sec.jpg")
image = cv2.imread("./test_images/polar_30sec.jpg")
# image = cv2.imread("./test_images/sagitario_10sec_gain_max.jpg")
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
    print(f'{area=}')
    print(f'{perimeter=}')

    epsilon = 0.02 * area
    approx = cv2.approxPolyDP(c, epsilon, True)

    # Mean of ROI
    mean = cv2.mean(c)

    # draw the contour and center of the shape on the image
    cv2.drawContours(image, [approx], -1, (51, 255, 255), 1)
    # cv2.drawContours(image, [approx], -1, (51, 255, 255), 1)
    #cv2.circle(image, (cX, cY), 3, (255, 255, 255), -1)
    cv2.putText(image, str(i), (cX + 1, cY + 1),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # k = cv2.waitKey(0)
    # if k == 113:
    #     sys.exit(0)
    i += 1

    # (x,y),radius = cv2.minEnclosingCircle(c)
    # center = (int(x),int(y))
    # radius = int(radius)
    # cv2.circle(image,center,radius,(0,255,0),1)
    # show the image
    cv2.imshow("Image", image)

# show the plotting graph of an image
plt.plot(hist)
plt.show()


print("Stars found:", len(cnts)-invalid)
while True:
    k = cv2.waitKey(0)
    if k == 113:
        sys.exit(0)
        # 113 -> q
        # 32  -> space
