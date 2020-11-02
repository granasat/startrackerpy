#!/usr/bin/env python
import argparse
import csv
import math
from novas import compat as novas
from utils import CatEntry


def data_complete(star):
    """Checks if the star has the required data"""
    try:
        float(star[8])
    except ValueError:
        return False

    return True


def deg_to_time(degress):
    """Converts a given degrees into time format"""
    decimal_time = deg_to_decimal_time(degress)
    hours = int(decimal_time)
    minutes = int((decimal_time*60) % 60)
    seconds = (decimal_time*3600) % 60

    return f"{hours} {minutes} {seconds:.2f}"


def deg_to_decimal_time(degrees):
    """Converts a given degrees into decimal time float"""
    return degrees / 15.0


def decimal_time_to_degrees(decimal_time):
    """Converts a given decimal time into degrees"""
    return decimal_time * 15.0


def deg_to_deg_min_sec(degrees):
    """Convert decimal degrees to degress, minutes and seconds"""
    d = int(degrees)
    minutes = int((degrees - d) * 60)
    seconds = (degrees - d - minutes / 60) * 3600

    # Append a '+' for positive degrees
    if d >= 0:
        return f"+{d:02d} {minutes} {seconds:.1f}"

    return f"{d:03d} {minutes} {seconds:.1f}"


def deg_min_sec_to_dec_deg(deg_min_sec):
    """Convert Degrees minutes and seconds.ms to decimal degrees"""
    deg = int(deg_min_sec.split(' ')[0])
    min = int(deg_min_sec.split(' ')[1])
    sec = float(deg_min_sec.split(' ')[2])

    dec_deg = abs(deg) + min/60 + sec/3600
    dec_deg = round(dec_deg, 8)

    if deg < 0:
        return -dec_deg
    return dec_deg

def main(args):
    date = args.date.split(' ')
    leap_secs = 37
    epoc_hip = 2448349.0625
    # Date to convert the catalog to
    jd_utc = novas.julian_date(int(date[0]), int(date[1]),
                               int(date[2]), float(date[3]))
    jd_tt = jd_utc + (leap_secs + 32.184) / 86400
    # jd_tt = novas.julian_date(1991, 4, 2, 12.5)
    converted = []

    # Read the original catalog content
    with open(args.input, 'r') as raw:
        content = [
            [field.strip() for field in line.split()]
            for line in raw
        ]

    for line in content:
        if not data_complete(line):
            continue
        ra_degrees = float(line[4]) * 180 / math.pi
        ra_hours = deg_to_decimal_time(ra_degrees)
        dec_degrees = float(line[5]) * 180 / math.pi
        parallax = float(line[6]) if float(line[6]) > 0 else 0.0
        vmag = float(line[19])
        star = novas.make_cat_entry(line[0], "HIP", int(line[0]),
                                    ra_hours, dec_degrees,
                                    float(line[7]), float(line[8]),
                                    parallax, 0.0)

        star_con = novas.transform_cat(1, epoc_hip, star, jd_tt, "HP2")
        star_entry = CatEntry(star_con.starname, star_con.catalog,
                              star_con.starnumber, star_con.ra,
                              star_con.dec, star_con.promora,
                              star_con.promodec, star_con.parallax,
                              star_con.radialvelocity, vmag)
        converted.append(star_entry)

    # Write new catalog into a file
    with open(args.output, mode='w') as csv_file:
        fieldnames = ['HIP_number', 'ra_degrees', 'dec_degrees',
                      'promora', 'promodec', 'parallax', 'vmag']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for star in converted:
            writer.writerow({
                'HIP_number': star.starnumber,
                'ra_degrees': "{0:.8f}".format(decimal_time_to_degrees(star.ra)),
                'dec_degrees': "{0:.8f}".format(star.dec),
                'promora': "{0:.8f}".format(star.promora),
                'promodec': "{0:.8f}".format(star.promodec),
                'parallax': "{0:.8f}".format(star.parallax),
                'vmag': "{0:.2f}".format(star.vmag),
            })

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', required=True, dest='input',
                        help='Hipparcos I311 input .dat file')
    parser.add_argument('-o', '--output', required=True, dest='output',
                        help='Output CSV converted path')
    parser.add_argument('-d', '--date', required=True, dest='date',
                        help='Date to convert to: "2020 8 21 12.5"')

    main(parser.parse_args())
