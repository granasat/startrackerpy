#!/usr/bin/env python3
import imutils
from io import BytesIO
from scipy.stats import norm
import cv2
import numpy as np
from server import catalog
from server.startracker.image_star import ImageStar, Centroid
import matplotlib.pyplot as plt
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.wcs.utils import fit_wcs_from_points
import logging



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
        logging.warning(f'{mean=} {std=}')
        formula = 0.606 * mean + std + 2.85 -0.79
        logging.warning(f'{formula=}')
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
        # Connect first and last too
        cv2.line(img, (int(stars[0].centroid.x), int(stars[0].centroid.y)),
                     (int(stars[-1].centroid.x), int(stars[-1].centroid.y)),
                     color, 1)

        # Put name for identified stars
        for star in stars:
            if star.is_identified():
                center = (star.centroid.x - 20, star.centroid.y - 10)
                cv2.putText(img, str(star.real_star.name), center,
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)

    @classmethod
    def draw_guide_stars(cls, img, img_stars, pattern, max=20, color=(255, 255, 255)):
        """Given an image and a list of Centroids
        draw lines in the image between them in order"""
        # Build WCS
        pixels_x = np.array([])
        pixels_y = np.array([])
        stars_ra = []
        stars_dec = []
        for found_star in pattern:
            if found_star.is_identified():
                pixels_x = np.append(pixels_x, found_star.centroid.x)
                pixels_y = np.append(pixels_y, found_star.centroid.y)
                stars_ra.append(found_star.real_star.ra)
                stars_dec.append(found_star.real_star.dec)
        stars = SkyCoord(ra=stars_ra, dec=stars_dec, unit=u.deg)
        wcs = fit_wcs_from_points((pixels_x, pixels_y), stars)

        img_stars_to_label = []
        for img_star in img_stars:
            for found_star in pattern:
                if found_star.centroid == img_star.centroid and found_star.is_identified():
                    img_star.labeled = True
            img_stars_to_label.append(img_star)

        # Set wcs coordinates to ImageStars
        for img_star in img_stars:
            pixel_x = np.array([[img_star.centroid.x]])
            pixel_y = np.array([[img_star.centroid.y]])
            coords_ra, coords_dec = wcs.wcs_pix2world(pixel_x, pixel_y, 0)
            coords = SkyCoord(ra=coords_ra, dec=coords_dec, unit=u.deg)
            img_star.set_wcs_coords(coords)

        labeled = 0
        for hip_number in catalog._guide_stars:
            star = catalog.get_star_by_id(int(hip_number))
            coords_a = SkyCoord(ra=star.ra, dec=star.dec, unit=u.deg)
            max = 10
            for img_star in img_stars_to_label[:max]:
                if img_star.is_labeled():
                    continue
                coords_b = img_star.get_wcs_coords()
                if coords_a.separation(coords_b) < 0.5 * u.deg:
                    center = (img_star.centroid.x - 20, img_star.centroid.y + 25)
                    cv2.putText(img, str(star.name), center,
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 1)
                    labeled += 1
                    img_star.set_labeled()

        return labeled
