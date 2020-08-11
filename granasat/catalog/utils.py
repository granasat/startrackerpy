from typing import NamedTuple
import math
import numpy as np


class CatEntry(NamedTuple):
    """Represents a catalog entry"""
    starname: str
    catalog: str
    starnumber: int
    ra: float
    dec: float
    promora: float
    promodec: float
    parallax: float
    radialvelocity: float
    vmag: float


def convertRADEC(ra, dec):
    """Converts the given ra and dec to its cartesian coordinates"""
    r = 1
    x = r * math.sin(np.deg2rad(dec)) * math.cos(np.deg2rad(ra))
    y = r * math.sin(np.deg2rad(dec)) * math.sin(np.deg2rad(ra))
    z = r * math.cos(np.deg2rad(dec))

    return [x, y, z]
