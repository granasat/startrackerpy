#!/usr/bin/env python3
import argparse
import csv


def generate_k_vector(guide_catalog):
    k_vector = []
    z = []
    n = len(guide_catalog)
    m = (guide_catalog[-1][2]-guide_catalog[0][2])/(n-1)
    q = guide_catalog[0][2]-m

    k_vector.append(0)
    for i in range(0, n):
        z.append(i*m+q)

    for j in range(1, n-1):
        number = len([i for i in guide_catalog if i[2] < z[j]])
        k_vector.append(number)

    k_vector.append(n)

    return k_vector


def read_catalog(catalog_csv):
    catalog = []
    with open(catalog_csv, 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        line_count = 0
        for row in csv_reader:
            if line_count != 0:
                catalog.append([int(row['HIP_number_a']),
                                int(row['HIP_number_b']),
                                float(row['distance'])
                                ])
            line_count += 1

    return catalog


def main(args):
    catalog = read_catalog(args.input)
    k_vector = generate_k_vector(catalog)
    with open(args.output, mode='w') as csv_file:
        fieldnames = ['stars_count']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for total_stars in k_vector:
            writer.writerow({'stars_count': total_stars})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', required=True, dest='input',
                        help='Sorted guide catalog input CSV path')
    parser.add_argument('-o', '--output', required=True, dest='output',
                        help='Output k-vector csv')

    main(parser.parse_args())
