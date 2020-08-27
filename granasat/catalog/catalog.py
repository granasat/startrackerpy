#!/usr/bin/env python3
import csv
import json
import numpy as np
from star import Star
from image_star import ImageStar

class Catalog:
    def __init__(self, hip_csv, guide_stars_csv, guide_stars_labels_csv=None,
                 guide_neighbours_json=None):
        self._hip_catalog = {}
        self._guide_stars = []
        self._guide_stars_catalog = []
        self._guide_neighbours_catalog = {}
        self._fov_catalog = []
        self._load_hip_catalog(hip_csv)
        self._load_guide_stars_catalog(guide_stars_csv)
        self._label_guide_stars(guide_stars_labels_csv)
        if guide_neighbours_json is not None:
            self._load_guide_neighbours_catalog(guide_neighbours_json)
        # self.generate_fov_catalog()

    def _load_hip_catalog(self, hip_csv):
        """Main catalog in a dictionary and a Star object"""
        with open(hip_csv, 'r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                star = Star(row['HIP_number'], float(row['ra_degrees']),
                            float(row['dec_degrees']), row['promora'],
                            row['promodec'], row['parallax'],
                            float(row['vmag']))
                self._hip_catalog[row['HIP_number']] = star

    def _load_guide_stars_catalog(self, guide_stars_csv):
        lst = []
        with open(guide_stars_csv, 'r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                hip_a = int(row["HIP_number_a"])
                hip_b = int(row["HIP_number_b"])
                distance = float(row["distance"])
                lst.append([hip_a, hip_b, distance])
        self._guide_stars_catalog = np.array(lst)
        self._guide_stars = np.unique(self._guide_stars_catalog[:, :-1])

    def _label_guide_stars(self, guide_stars_labels_csv):
        with open(guide_stars_labels_csv, 'r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                self._hip_catalog[row['HIP_number']].set_name(row['Name'])

    def _load_guide_neighbours_catalog(self, json_file_path):
        with open(json_file_path, 'r') as json_file:
            data = json_file.read()
        self._guide_neighbours_catalog = json.loads(data)

    def generate_fov_catalog(self):
        for star_id in self._guide_neighbours_catalog:
            # Discard stars with less than 3 neighbours
            if len(self._guide_neighbours_catalog[star_id]) < 3:
                continue

            star = self._hip_catalog[star_id]
            for neighbour in self._guide_neighbours_catalog[star_id]:
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
            # Sort them by star hip_number
            self._fov_catalog = sorted(self._fov_catalog, key=lambda x: int(x[0].hip_number))

    def get_star_by_id(self, hip_number):
        if str(hip_number) in self._hip_catalog:
            return self._hip_catalog[str(hip_number)]

        return None

    def get_pairs_by_distance(self, a, b):
        """Returns the pairs for which their angular distance
        is greater than a and lower than b"""
        # np.where((arr[:,2]>a) & (arr[:,2] < b))
        # would return the indices in arr matching the condition
        pairs = []
        condition = (self._guide_stars_catalog[:, 2] > a) & \
            (self._guide_stars_catalog[:, 2] < b)
        indices = np.where(condition)
        for i in indices[0]:
            pairs.append([int(self._guide_stars_catalog[i][0]),
                          int(self._guide_stars_catalog[i][1]),
                          float(self._guide_stars_catalog[i][2])])

        return pairs

    def get_most_brightness(self, star):
        """Given a start returns the three more brightness stars
        From its neighbours"""
        stars = star.get_neighbours() + [star]
        if len(stars) < 3:
            return []
        return sorted(stars, key=lambda x: x.vmag)[:3]

    def get_triplets_of_triangle(self, triangle, threshold=0.005):
        """The kernel will always be the triangle[0] ImageStar"""
        star1, star2, star3 = triangle
        triplets = []

        d_star1_star2 = star1.get_distance(star2)
        d_star1_star3 = star1.get_distance(star3)
        d_star2_star3 = star2.get_distance(star3)

        # This is the error allowed for the distances
        # threshold is a percentage of the error allowed
        err1 = d_star1_star2 * threshold
        err2 = d_star1_star3 * threshold
        err3 = d_star2_star3 * threshold

        pairs_a_b = self.get_pairs_by_distance(d_star1_star2-err1, d_star1_star2+err1)
        pairs_a_c = self.get_pairs_by_distance(d_star1_star3-err2, d_star1_star3+err2)

        # For each star present in both pairs AB and AC
        # Check if the other two stars are in range of
        # distance BC star2_star3
        for pair1 in pairs_a_b:
            for pair2 in pairs_a_c:
                hip_both = None  # This is the star present in both pairs
                if pair1[0] == pair2[0]:
                    hip_both = pair1[0]
                    hip_x = pair1[1]
                    hip_y = pair2[1]
                elif pair1[0] == pair2[1]:
                    hip_both = pair1[0]
                    hip_x = pair1[1]
                    hip_y = pair2[0]
                elif pair1[1] == pair2[0]:
                    hip_both = pair1[1]
                    hip_x = pair1[0]
                    hip_y = pair2[1]
                elif pair1[1] == pair2[1]:
                    hip_both = pair1[1]
                    hip_x = pair1[0]
                    hip_y = pair2[0]
                else:
                    continue

                star_x = ImageStar(star2.centroid, star2.brightness)
                star_y = ImageStar(star3.centroid, star3.brightness)
                star_both = ImageStar(star1.centroid, star1.brightness)
                star_x.set_real_star(self.get_star_by_id(hip_x))
                star_y.set_real_star(self.get_star_by_id(hip_y))
                star_both.set_real_star(self.get_star_by_id(hip_both))
                other_distance = star_x.real_star.get_distance(star_y.real_star)
                # Distance BC-threshold < others_distance < BC+threshold
                if d_star2_star3-err3 < other_distance < d_star2_star3+err3:
                    triplets.append([star_x, star_y, star_both])

        return triplets

    def find_star_pattern(self, img_stars, threshold=0.005):
        """
        threshold: degrees to extend the angular distance to"""
        # Get the first three image stars (most brightness)
        star1 = img_stars[0]  # ImageStar A
        star2 = img_stars[1]  # ImageStar B
        star3 = img_stars[2]  # ImageStar C
        triplets = {}

        triplets['kernel_A'] = self.get_triplets_of_triangle([star1, star2, star3], threshold=threshold)
        triplets['kernel_B'] = self.get_triplets_of_triangle([star2, star1, star3], threshold=threshold)
        triplets['kernel_C'] = self.get_triplets_of_triangle([star3, star2, star1], threshold=threshold)

        # Sort them
        triplets['kernel_A'] = [sorted(i, key=lambda x: x.real_star.hip_number) for i in triplets['kernel_A']]
        triplets['kernel_B'] = [sorted(i, key=lambda x: x.real_star.hip_number) for i in triplets['kernel_B']]
        triplets['kernel_C'] = [sorted(i, key=lambda x: x.real_star.hip_number) for i in triplets['kernel_C']]
        unique = []

        # Select only the triplets in all kernels
        for i in triplets['kernel_A']:
            if i in triplets['kernel_B'] and i in triplets['kernel_C']:
                unique.append(i)

        return unique


    def get_common_stars(self, triplets_a, triplets_b):
        """Having two list of triplets of stars as parameters
        return the stars which are in both triplets

        basically, search if for any triplet in a there is a triplet in b which
        contains two elements of the former one. In this case we have found
        4 real stars, 2 of them we can identify their possition in the image,
        the other two we are not sure (50%).

        returns [[ImageStar, ImageStar], [Star, Star]]
        """

        common = []
        news = []
        for triplet_i in triplets_a:
            for triplet_j in triplets_b:
                if (triplet_i[0] in triplet_j and triplet_i[1] in triplet_j) or \
                   (triplet_i[0] in triplet_j and triplet_i[2] in triplet_j) or \
                   (triplet_i[1] in triplet_j and triplet_i[2] in triplet_j):
                    # Add all stars from triplet_i and the new one from
                    # triplet_j
                    common = [star for star in triplet_i if star in triplet_j]
                    new_i = [star for star in triplet_i if star not in triplet_j]
                    new_j = [star for star in triplet_j if star not in triplet_i]
                    news = new_i + new_j

        return [common, news]


# catalog = Catalog("./generation/out/hip_2000.csv", "./generation/out/guide_stars_2000_5.csv", "./generation/out/guide_stars_2000_5_labels.csv")
