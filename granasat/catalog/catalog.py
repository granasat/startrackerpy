#!/usr/bin/env python3
import csv
import json
import numpy as np
from star import Star


class Catalog:
    def __init__(self, hip_csv, guide_stars_json):
        self._hip_catalog = {}
        self._guide_catalog = {}
        self._fov_catalog = []
        self._load_hip_catalog(hip_csv)
        self._load_guide_catalog(guide_stars_json)
        self._generate_fov_catalog()

    def _load_hip_catalog(self, hip_csv):
        """Note: we add +90 degrees to the declination"""
        with open(hip_csv, 'r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            headers_line = True
            for row in csv_reader:
                if headers_line:
                    headers_line = False
                    continue
                star = Star(row['HIP_number'], float(row['ra_degrees']),
                            float(row['dec_degrees'])+90, row['promora'],
                            row['promodec'], row['parallax'],
                            float(row['vmag']))
                self._hip_catalog[row['HIP_number']] = star

    def _load_guide_catalog(self, json_file_path):
        with open(json_file_path, 'r') as json_file:
            data = json_file.read()
        self._guide_catalog = json.loads(data)

    def _generate_fov_catalog(self):
        for star_id in self._guide_catalog:
            # Discard stars with less than 3 neighbours
            if len(self._guide_catalog[star_id]) < 3:
                continue

            star = self._hip_catalog[star_id]
            for neighbour in self._guide_catalog[star_id]:
                star.add_neighbour(self._hip_catalog[neighbour])

            # Get the three most brightness neighbours
            most_brightness = self.get_most_brightness(star)

            # Get their cartesian coordinates
            star1 = most_brightness[0].get_cartesian_coords()
            star2 = most_brightness[1].get_cartesian_coords()
            star3 = most_brightness[2].get_cartesian_coords()

            # Calculate the three vectors between them
            v1 = np.subtract(star2, star1)
            v2 = np.subtract(star3, star1)
            v3 = np.subtract(star3, star2)

            # Calculate the 3 angles of the triangle
            angle1 = np.dot(v1, v2)/(np.linalg.norm(v1)*np.linalg.norm(v2))
            angle2 = np.dot(-v1, v3)/(np.linalg.norm(v1)*np.linalg.norm(v3))
            angle3 = np.dot(-v2, -v3)/(np.linalg.norm(v2)*np.linalg.norm(v3))
            triad = [angle1, angle2, angle3]

            # Get the shortest and longest vectors
            sorted_vectors = sorted([v1, v2, v3], key=np.linalg.norm)
            v_min = sorted_vectors[0].tolist()
            v_max = sorted_vectors[2].tolist()

            # Obtain the sign of the coefficient
            rotation = np.sign(np.dot(v_min, v_max) /
                               (np.linalg.norm(v_min)*np.linalg.norm(v_max)))

            # Calculate the coefficient
            c = np.cross(v_min, v_max)
            coef = rotation*np.linalg.norm(c)
            self._fov_catalog.append([star, most_brightness, triad, coef])

    def get_most_brightness(self, star):
        # Given a start returns the three more brightness stars
        stars = star.get_neighbours() + [star]
        if len(stars) < 3:
            return []
        return sorted(stars, key=lambda x: x.vmag)[:3]



catalog = Catalog("./generation/out/hip_2020.csv", "./generation/out/guide_stars_neighboors_6.json")
