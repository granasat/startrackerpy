import math
import numpy as np


class Star:
    """Represents a star and provides methods to convert coordinates,
    save a list of neighboors..."""
    def __init__(self, hip_number, ra, dec, promora, promodec, parallax, vmag):
        self.hip_number = hip_number
        self.ra = ra
        self.dec = dec
        self.promora = promora
        self.promodec = promodec
        self.parallax = parallax
        self.vmag = vmag
        self._neighbours = []

    def add_neighbour(self, star):
        self._neighbours.append(star)

    def get_neighbours(self):
        return self._neighbours

    def get_cartesian_coords(self):
        """Converts the given ra and dec to its cartesian coordinates"""
        r = 1
        x = r * math.sin(np.deg2rad(self.dec)) * math.cos(np.deg2rad(self.ra))
        y = r * math.sin(np.deg2rad(self.dec)) * math.sin(np.deg2rad(self.ra))
        z = r * math.cos(np.deg2rad(self.dec))

        return [x, y, z]
