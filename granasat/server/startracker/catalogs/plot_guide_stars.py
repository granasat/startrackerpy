#!/usr/bin/env python3
import csv
from utils import convertRADEC
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import axes3d


def read_hip_catalog(catalog_csv):
    hip_catalog = {}
    with open(catalog_csv, 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        line_count = 0
        for row in csv_reader:
            if line_count != 0:
                hip_catalog[row['HIP_number']] = [
                    row['ra_degrees'],
                    row['dec_degrees'],
                    row['promora'],
                    row['promodec'],
                    row['parallax'],
                    row['vmag']
                ]
            line_count += 1
    return hip_catalog



def read_guide_catalog(catalog_csv):
    guide_catalog = []
    with open(catalog_csv, 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        line_count = 0
        for row in csv_reader:
            if line_count != 0:
                guide_catalog.append([row['HIP_number_a'],
                                      row['HIP_number_a'],
                                      row['distance']])
            line_count += 1
    return guide_catalog


def main():
    hip_catalog = read_hip_catalog("./out/hip_2020.csv")
    guide_catalog = read_guide_catalog("./out/guide_stars_2020.csv")
    guide_stars = [set(x) for x in zip(*guide_catalog)][0]
    stars_car = []

    for star in guide_stars:
        if star == "49669":
            print(star)
            print(hip_catalog[star])
        star_ra = float(hip_catalog[star][0])
        star_dec = float(hip_catalog[star][1])
        star_car = convertRADEC(star_ra, star_dec + 90)
        stars_car.append(star_car)

    print(guide_stars)
    print(stars_car[0])
    print(stars_car[200])
    plt.figure()
    ax = plt.axes(projection="3d")
    list_zip = [x for x in zip(*stars_car)]
    ax.scatter(list_zip[0], list_zip[1], list_zip[2], color='g')
    # Draw grid lines with color and dashed style
    ax.set_xlabel('X Axes')
    ax.set_ylabel('Y Axes')
    ax.set_zlabel('Z Axes')

    plt.show()


if __name__ == "__main__":
    main()
