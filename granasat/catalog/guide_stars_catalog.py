#!/usr/bin/env python3
import math
import argparse
import itertools
import csv
from utils import CatEntry, convertRADEC


def generate_guide_catalog(catalog):
    """Generate a catalog with the angular distance of all stars
    combinations"""
    guide_catalog = []
    FOV_h = 2 * 14.455
    FOV_v = 2 * 10.94
    FOV = math.sqrt(FOV_h**2 + FOV_v**2)

    for a, b in itertools.combinations(catalog, 2):
        a_car = convertRADEC(a.ra, a.dec + 90)
        b_car = convertRADEC(b.ra, b.dec + 90)
        dab = math.degrees(math.acos(a_car[0] * b_car[0] +
                                     a_car[1] * b_car[1] +
                                     a_car[2] * b_car[2]))

        if dab < FOV:
            guide_catalog.append([a.starnumber, b.starnumber, dab])

    guide_catalog.sort(key=lambda x: x[2])
    return guide_catalog


def read_catalog(catalog_csv, CVmag):
    """Read the propagated catalog and filter out stars with Vmag greater than
    CVmag"""
    catalog = []
    with open(catalog_csv, 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        line_count = 0
        for row in csv_reader:
            if line_count != 0:
                if float(row['vmag']) >= CVmag:
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
    catalog = read_catalog(args.input, float(args.cv_mag))
    guide_stars = generate_guide_catalog(catalog)
    with open(args.output, mode='w') as csv_file:
        fieldnames = ['HIP_number_a', 'HIP_number_b', 'distance']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in guide_stars:
            writer.writerow({
                'HIP_number_a': row[0],
                'HIP_number_b': row[1],
                'distance': row[2]
            })


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', required=True, dest='input',
                        help='Hipparcos input CSV path')
    parser.add_argument('-o', '--output', required=True, dest='output',
                        help='Output CSV converted path')
    parser.add_argument('-m', '--magnitude', required=True, dest='cv_mag',
                        help='CVmag threshold')

    main(parser.parse_args())
