#!/usr/bin/env python3
import math
import argparse
import itertools
import csv
import time
import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from astroquery.simbad import Simbad
from os.path import splitext
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
                                int(row['HIP_number']), float(row['ra_degrees']),
                                float(row['dec_degrees']), row['promora'],
                                row['promodec'], row['parallax'],
                                0.0, float(row['vmag']))
                catalog.append(star)
            line_count += 1
    return catalog

def label_guide_stars(filename, catalog, guide_stars):
    stars = np.array(guide_stars)
    # Get unique guide_stars
    unique = np.unique(stars[:,:-1])
    hip_names = []
    checked = 0
    labeled = 0
    # Need a tuple of [HIP_number, ra, dec] for all guide stars
    for hip_star in catalog:
        # Stop earlier if all guide stars are already labeled.
        if checked == len(unique):
            break
        if hip_star.starnumber in unique:
            # Query Simbad for its object, then name
            c = SkyCoord(ra=hip_star.ra, dec=hip_star.dec, unit=u.deg)
            print(c)
            while True:
                try:
                    reg = Simbad.query_region(c, radius=0.01*u.deg)
                except:
                    time.sleep(5)
                    continue
                break
            name = ""
            if len(reg[0]) > 0:
                while True:
                    try:
                        objs = Simbad.query_objectids(reg[0][0])
                    except:
                        time.sleep(5)
                        continue
                    break
                if len(objs) > 0:
                    noname = True
                    for name in objs:
                        if "NAME" in name[0]:
                            name = name[0].replace("NAME", "").strip().lower()
                            noname = False
                            labeled += 1
                            print(name)
                            break
                    if noname:
                        name = str(hip_star.starnumber)

            time.sleep(0.2)
            hip_names.append([hip_star.starnumber, name])
            checked += 1
            print(f'{checked=} {labeled=}')

    with open(filename, mode='w') as csv_file:
        fieldnames = ['HIP_number', 'Name']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for star in hip_names:
            writer.writerow({'HIP_number': star[0], 'Name': star[1]})


def main(args):
    catalog = read_catalog(args.input, float(args.v_mag))
    guide_stars = generate_guide_catalog(catalog)
    split_name = splitext(args.output)

    # Write guide stars pairs with their angular distance
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
    # Write a file with labels for each guide star
    labels_filename = split_name[0] + "_labels" + split_name[1]
    label_guide_stars(labels_filename, catalog, guide_stars)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', required=True, dest='input',
                        help='Hipparcos input CSV path')
    parser.add_argument('-o', '--output', required=True, dest='output',
                        help='Output CSV converted path')
    parser.add_argument('-m', '--magnitude', required=True, dest='v_mag',
                        help='Vmag cutoff')

    main(parser.parse_args())
