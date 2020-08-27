import math
import numpy as np
from astropy.coordinates import SkyCoord
from astropy import units as u


class Star:
    """Represents a star and provides methods to convert coordinates,
    save a list of neighboors..."""
    def __init__(self, hip_number, ra, dec, promora, promodec, parallax, vmag):
        self.hip_number = hip_number
        self.name = ""
        self.ra = ra
        self.dec = dec
        self.promora = promora
        self.promodec = promodec
        self.parallax = parallax
        self.vmag = vmag
        self._neighbours = []

    def __eq__(self, other):
        return self.hip_number == other.hip_number

    def __repr__(self):
        return self.hip_number

    def __str__(self):
        return self.hip_number

    def add_neighbour(self, star):
        self._neighbours.append(star)

    def get_neighbours(self):
        return self._neighbours

    def get_cartesian_coords(self):
        """Converts the given ra and dec to its cartesian coordinates"""
        r = 1
        dec = self.dec + 90
        x = r * math.sin(np.deg2rad(dec)) * math.cos(np.deg2rad(self.ra))
        y = r * math.sin(np.deg2rad(dec)) * math.sin(np.deg2rad(self.ra))
        z = r * math.cos(np.deg2rad(dec))

        return [x, y, z]

    def get_distance(self, star):
        """Returns the angular distance to the given star"""
        if self == star:
            return 0

        a_car = self.get_cartesian_coords()
        b_car = star.get_cartesian_coords()
        dab = math.degrees(math.acos(a_car[0] * b_car[0] +
                                     a_car[1] * b_car[1] +
                                     a_car[2] * b_car[2]))
        return dab

    def set_name(self, name):
        self.name = name
