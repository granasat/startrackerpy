#!/usr/bin/env python3
import cv2
import imutils
import matplotlib.pyplot as plt
from scipy.stats import norm
from scipy import signal
import numpy as np
from math import sqrt
from scipy.ndimage import label


def simple_thinning(strength):
    [r, c] = strength.shape

    # np.zeros((1, c), dtype=int)

    # Delete last column 1280 of 1280 # WORKS
    zero_last_col = np.concatenate((np.zeros((r, 1)),
                                    np.delete(strength, -1, 1)), axis=1)

    # Delete first column 0 of 1280
    zero_first_col = np.concatenate((np.delete(strength, 0, 1),
                                     np.zeros((r, 1))), axis=1)


    # Delete last row 960 of 960, zeros in first row
    zero_first_row = np.concatenate((np.zeros((1, c)),
                                     np.delete(strength, -1, 0)), axis=0)
    # Delete first row 960 of 960, zeros in last row
    zero_last_row = np.concatenate((np.delete(strength, 0, 0),
                                    np.zeros((1, c))), axis=0)

    x = np.where(np.logical_and(strength > zero_last_col, strength > zero_first_col), 1, 0)
    y = np.where(np.logical_and(strength > zero_first_row, strength > zero_last_row), 1, 0)

    bw = np.bitwise_or(x, y)

    return bw



assets_dir = "/home/igarcia/Nextcloud/University/TFG/reports/assets"
image = cv2.imread("./test_images/polar_05sec.jpg")

# Grayscale
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Manually apply sobel
h1 = np.array([[1, 2, 1], [0, 0, 0], [-1, -2, -1]])
h3 = h1.transpose()

h1_conv = signal.convolve2d(gray, h1, 'same') ** 2
h3_conv = signal.convolve2d(gray, h3, 'same') ** 2
strength = np.sqrt(h1_conv + h3_conv)

# Get threshold
thresh = 0.2

strength = np.where(strength <= thresh, 0, strength)

bw = simple_thinning(strength)

L = label(bw, np.array([[1, 1, 1], [1, 1, 1], [1, 1, 1]]))
