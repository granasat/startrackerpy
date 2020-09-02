#!/usr/bin/env python3
import imutils
from io import BytesIO
from scipy.stats import norm
import cv2
import numpy as np
from server.startracker.image_star import ImageStar, Centroid
import matplotlib.pyplot as plt


class ImageUtils:
    def __init__(self) -> None:
        pass

    @classmethod
    def get_threshold(cls, img, thresh_max=170):
        """Get the threshold value analyzing the normal distribution of
        the image's histogram

        :param img: Image to analyze
        :param thresh_max: Maximum value for threshold as limit
        """
        mean, std = norm.fit(img)
        threshold = int(mean + 3.6 * std)
        if thresh_max:
            threshold = threshold if threshold < thresh_max else thresh_max

        return threshold

    @classmethod
    def get_image_stars(cls, img, gray):
        """Return the ImageStar objects found in a thresholded image

        :param img: thresholded image to analyze
        :param gray: grayscale version of the original image"""

        img_stars = []
        cnts = cv2.findContours(img.copy(), cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        for c in cnts:
            M = cv2.moments(c)

            # Area of contour
            area = M["m00"]

            # Discard stars with area lesser than 3
            if area < 3:
                continue

            # Centroid of contour
            centroid = Centroid(int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

            # Perimeter
            perimeter = cv2.arcLength(c, True)

            # Polygon approximation
            epsilon = 0.01 * area
            approx = cv2.approxPolyDP(c, epsilon, True)

            # Create blank image
            blank_image = np.zeros(gray.shape, np.uint8)

            # Draw contour in the mask
            cv2.drawContours(blank_image, [approx], -1, (255, 255, 255), -1)

            # Create a mask to select pixels inside the figure
            mask_contour = blank_image == 255

            # Calculate the intensity from the grayscale image
            mean = np.mean(gray[mask_contour])
            brightness = mean
            # brightness = mean**3 + area * perimeter

            img_stars.append(ImageStar(centroid, brightness, perimeter, area))

        img_stars = sorted(img_stars, key=lambda x: x.brightness, reverse=True)
        return img_stars

    @classmethod
    def get_histogram_bytes(cls, img):
        # Histogram
        hist = cv2.calcHist([img], [0], None, [256], [0, 256])
        buf = BytesIO()
        plt.plot(hist)
        plt.savefig(buf, format='png')
        buf.seek(0)
        hist_bytes = buf.read()

        return hist_bytes

    @classmethod
    def draw_pattern(cls, img, stars, color=(0, 255, 0)):
        """Given an image and a list of Centroids
        draw lines in the image between them in order"""
        for star1, star2 in zip(stars, stars[1:]):
            cv2.line(img, (int(star1.centroid.x), int(star1.centroid.y)),
                     (int(star2.centroid.x), int(star2.centroid.y)),
                     color, 1)
            center = (star1.centroid.x - 20, star1.centroid.y - 10)
            cv2.putText(img, str(star1.real_star.name), center,
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
            center = (star2.centroid.x - 20, star2.centroid.y - 10)
            cv2.putText(img, str(star2.real_star.name), center,
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
        # Connect first and last too
        cv2.line(img, (int(stars[0].centroid.x), int(stars[0].centroid.y)),
                     (int(stars[-1].centroid.x), int(stars[-1].centroid.y)),
                     color, 1)
