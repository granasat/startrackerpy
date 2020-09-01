import math
import numpy as np
from math import cos, atan, atan2, sin, sqrt, pi

class Centroid:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class ImageStar:
    """Represents an image star"""
    FOCAL_LENGTH = 2657.33
    CENTER_X = 666
    CENTER_Y = 440

    def __init__(self, centroid, brightness, perimeter=0.0, area=0.0):
        self.centroid = centroid
        self.brightness = brightness
        self.perimeter = perimeter
        self.area = area
        self.real_star = None
        self.wcs_coords = None
        self.labeled = False

    def __eq__(self, other):
        if self.real_star is None or other.real_star is None:
            return False
        return self.real_star.hip_number == other.real_star.hip_number

    def __repr__(self):
        # return f"[{self.centroid.x}, {self.centroid.y}, {self.real_star}]"
        if self.real_star is not None:
            return f"{self.real_star.hip_number}"
        return f"x: {self.centroid.x}, y: {self.centroid.y}"

    def get_unitary_vector(self):
        f = self.FOCAL_LENGTH
        x = self.centroid.x - self.CENTER_X
        y = self.centroid.y - self.CENTER_Y
        x_u = cos(atan2(y, x)) * cos(pi/2 - atan(sqrt(pow(x/f, 2)+pow(y/f, 2))))
        y_u = sin(atan2(y, x)) * cos(pi/2 - atan(sqrt(pow(x/f, 2)+pow(y/f, 2))))
        z_u = sin(pi/2 - atan(sqrt(pow(x/f, 2) + pow(y/f, 2))))

        return [x_u, y_u, z_u]

    def get_distance(self, star):
        """Return the angular distance between this star and the one given
        as parameter."""
        if self.centroid == star.centroid:
            print("distance for same star")
            return 0

        unitary_a = self.get_unitary_vector()
        unitary_b = star.get_unitary_vector()
        dab = math.degrees(math.acos(unitary_a[0] * unitary_b[0] +
                                     unitary_a[1] * unitary_b[1] +
                                     unitary_a[2] * unitary_b[2]))
        return dab

    def set_real_star(self, star):
        """Match this ImageStar with a real Star"""
        self.real_star = star

    def set_wcs_coords(self, coords):
        self.wcs_coords = coords

    def get_wcs_coords(self):
        return self.wcs_coords

    def set_labeled(self):
        self.labeled = True

    def is_labeled(self):
        return self.labeled
