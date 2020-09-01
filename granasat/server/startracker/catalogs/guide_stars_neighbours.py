#!/usr/bin/env python3
import math
import argparse
import itertools
import csv
import json
import numpy as np
from utils import CatEntry, convertRADEC


def generate_guide_stars(catalog):
    """Generate a catalog with the angular distance of all stars
    combinations"""
    guide_stars = {}
    FOV_h = 14.455 * math.pi/180
    FOV_v = 10.94 * math.pi/180
    FOV_diag = math.sqrt(FOV_h**2 + FOV_v**2)/2

    for a, b in itertools.combinations(catalog, 2):
        a_car = convertRADEC(a.ra, a.dec + 90)
        b_car = convertRADEC(b.ra, b.dec + 90)
        angle = math.acos(np.dot(a_car, b_car) /
                          (np.linalg.norm(a_car)*np.linalg.norm(b_car)))
        if angle < FOV_diag:
            if a.starnumber not in guide_stars:
                guide_stars[a.starnumber] = []
            if b.starnumber not in guide_stars:
                guide_stars[b.starnumber] = []
            guide_stars[a.starnumber].append(b.starnumber)
            guide_stars[b.starnumber].append(a.starnumber)

    return guide_stars


def read_catalog(catalog_csv, Vmag):
    """Read the propagated catalog and filter out stars with Vmag greater or
    equal than Vmag"""
    catalog = []
    with open(catalog_csv, 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        line_count = 0
        for row in csv_reader:
            if line_count != 0:
                if float(row['vmag']) >= Vmag:
                    continue
                star = CatEntry(row['HIP_number'], "HIP",
                                row['HIP_number'], float(row['ra_degrees']),
                                float(row['dec_degrees']), row['promora'],
                                row['promodec'], row['parallax'],
                                0.0, float(row['vmag']))
                catalog.append(star)
            line_count += 1
    return catalog


def main(args):
    catalog = read_catalog(args.input, float(args.v_mag))
    guide_stars = generate_guide_stars(catalog)
    i = 0
    for k in guide_stars:
        if len(guide_stars[k]) < 3:
            i += 1
    print("Using Vmag cutoff of:", args.v_mag)
    print("Total guide stars:", len(catalog))
    print("Total guide stars with 0 neighboors:", len(catalog)-len(guide_stars))
    print("Total guide stars with 1-2 neighboors:", i)
    print("Total guide stars with 3 or more neighboors:", len(guide_stars)-i)
    with open(args.output, mode='w') as json_file:
        json.dump(guide_stars, json_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', required=True, dest='input',
                        help='Hipparcos input CSV path')
    parser.add_argument('-o', '--output', required=True, dest='output',
                        help='Output JSON guide stars neiboorhood')
    parser.add_argument('-m', '--magnitude', required=True, dest='v_mag',
                        help='Vmag cutoff')

    main(parser.parse_args())
