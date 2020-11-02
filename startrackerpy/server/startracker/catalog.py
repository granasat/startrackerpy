#!/usr/bin/env python3
import csv
import json
import copy
import numpy as np
from server.startracker.star import Star
from server.startracker.image_star import ImageStar

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
        """Given a HIP number ID, returns its Star object"""
        if str(hip_number) in self._hip_catalog:
            return self._hip_catalog[str(hip_number)]

        return None

    def get_pairs_by_distance(self, a, b):
        """Returns the pairs for which their angular distance
        is greater than a and lower than b"""
        pairs = []
        condition = (self._guide_stars_catalog[:, 2] > a) & \
            (self._guide_stars_catalog[:, 2] < b)
        indices = np.where(condition)
        for i in indices[0]:
            pairs.append([int(self._guide_stars_catalog[i][0]),
                          int(self._guide_stars_catalog[i][1]),
                          float(self._guide_stars_catalog[i][2])])

        return pairs

    @classmethod
    def get_most_brightness(cls, star):
        """Given a start returns the three more brightness stars
        From its neighbours"""
        stars = star.get_neighbours() + [star]
        if len(stars) < 3:
            return []
        return sorted(stars, key=lambda x: x.vmag)[:3]

    def get_triplets_of_triangle(self, triangle, err=0.005):
        """The kernel will always be the triangle[0] ImageStar"""
        star1, star2, star3 = triangle
        triplets = []

        d_star1_star2 = star1.get_distance(star2)
        d_star1_star3 = star1.get_distance(star3)
        d_star2_star3 = star2.get_distance(star3)

        # This is the error allowed for the distances
        # threshold is a percentage of the error allowed
        err1 = d_star1_star2 * err
        err2 = d_star1_star3 * err
        err3 = d_star2_star3 * err

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

                star_x = ImageStar(star2.centroid, star2.brightness, star2.perimeter, star2.area)
                star_y = ImageStar(star3.centroid, star3.brightness, star3.perimeter, star3.area)
                star_both = ImageStar(star1.centroid, star1.brightness, star1.perimeter, star1.area)
                star_x.set_real_star(self.get_star_by_id(hip_x))
                star_y.set_real_star(self.get_star_by_id(hip_y))
                star_both.set_real_star(self.get_star_by_id(hip_both))
                other_distance = star_x.real_star.get_distance(star_y.real_star)
                # Distance BC-threshold < others_distance < BC+threshold
                if d_star2_star3-err3 < other_distance < d_star2_star3+err3:
                    triplets.append([star_x, star_y, star_both])

        return triplets

    def _get_triplets(self, img_stars, err=0.005):
        """
        threshold: degrees to extend the angular distance to"""
        # Get the first three image stars (most brightness)
        star1 = img_stars[0]  # ImageStar A
        star2 = img_stars[1]  # ImageStar B
        star3 = img_stars[2]  # ImageStar C

        triplets = {}

        triplets['kernel_A'] = self.get_triplets_of_triangle([star1, star2, star3], err=err)
        triplets['kernel_B'] = self.get_triplets_of_triangle([star2, star1, star3], err=err)
        triplets['kernel_C'] = self.get_triplets_of_triangle([star3, star2, star1], err=err)

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

    @classmethod
    def get_common_stars(cls, triplets_a, triplets_b):
        """Having two list of triplets of stars as parameters
        return the stars which are in both triplets

        basically, search if for any triplet in a there is a triplet in b which
        contains two elements of the former one. In this case we have found
        4 real stars, 2 of them we can identify their possition in the image,
        the other two we are not sure (50%).

        returns [[ImageStar, ImageStar], [...]]
        """

        common = []
        news = []
        for triplet_i in triplets_a:
            for triplet_j in triplets_b:
                if (triplet_i[0] in triplet_j and triplet_i[1] in triplet_j) or \
                   (triplet_i[0] in triplet_j and triplet_i[2] in triplet_j) or \
                   (triplet_i[1] in triplet_j and triplet_i[2] in triplet_j):
                    common.append(triplet_i + [star for star in triplet_j if star not in triplet_i])

        return [common, news]

    def _get_common_triplets(self, triplets_a, triplets_b) -> list:
        """Having two list of triplets of stars as parameters
        return the stars which are in both triplets having two in common.

        basically, search if for any triplet in 'a' there is a triplet in 'b'
        which contains two elements of the first one.

        returns List of ImageStar or empty list.
        """

        common = []
        for triplet_i in triplets_a:
            for triplet_j in triplets_b:
                if (triplet_i[0] in triplet_j and triplet_i[1] in triplet_j):
                    new_i = int(triplet_i[2].real_star.hip_number)
                    new_j = int(self._get_not_matched(triplet_j, [triplet_i[0], triplet_i[1]]).real_star.hip_number)
                    distance_index = np.where(((self._guide_stars_catalog[:,1] == new_i) &
                                               (self._guide_stars_catalog[:,0] == new_j)) |
                                              ((self._guide_stars_catalog[:,1] == new_j) &
                                               (self._guide_stars_catalog[:,0] == new_i)))
                    if len(distance_index[0]) > 0:
                        distance = self._guide_stars_catalog[distance_index[0][0]][2]
                        common.append(triplet_i + [star for star in triplet_j if star not in triplet_i])
                elif (triplet_i[0] in triplet_j and triplet_i[2] in triplet_j):
                    new_i = int(triplet_i[1].real_star.hip_number)
                    new_j = int(self._get_not_matched(triplet_j, [triplet_i[0], triplet_i[2]]).real_star.hip_number)
                    distance_index = np.where(((self._guide_stars_catalog[:,1] == new_i) &
                                               (self._guide_stars_catalog[:,0] == new_j)) |
                                              ((self._guide_stars_catalog[:,1] == new_j) &
                                               (self._guide_stars_catalog[:,0] == new_i)))
                    if len(distance_index[0]) > 0:
                        distance = self._guide_stars_catalog[distance_index[0][0]][2]
                        common.append(triplet_i + [star for star in triplet_j if star not in triplet_i])
                elif (triplet_i[1] in triplet_j and triplet_i[2] in triplet_j):
                    new_i = int(triplet_i[0].real_star.hip_number)
                    new_j = int(self._get_not_matched(triplet_j, [triplet_i[1], triplet_i[2]]).real_star.hip_number)
                    distance_index = np.where(((self._guide_stars_catalog[:,1] == new_i) &
                                               (self._guide_stars_catalog[:,0] == new_j)) |
                                              ((self._guide_stars_catalog[:,1] == new_j) &
                                               (self._guide_stars_catalog[:,0] == new_i)))
                    if len(distance_index[0]) > 0:
                        distance = self._guide_stars_catalog[distance_index[0][0]][2]
                        common.append(triplet_i + [star for star in triplet_j if star not in triplet_i])
        return common

    @classmethod
    def _get_common_quads(cls, lists):
        """lists of lists of quads of possible pattern solutions
            this function returns the ones appearing in both lists"""
        common = []
        for quad in lists[0]:
            exists = True
            for l2 in lists[1:]:
                in_this_list = False
                for quad2 in l2:
                    if quad2[0] in quad and quad2[1] in quad \
                       and quad2[2] in quad and quad2[3] in quad:
                        in_this_list = True
                        break
                if not in_this_list:
                    break
            if exists:
                common.append(quad)

        return common

    def _get_missing_star_from_triplets(self, triplets, pattern):
        """Given a list of triplets an a quad pattern, return the missing
        star from the pattern which has all the triplet stars."""
        for triplet in triplets:
            from_pattern = []
            for match in pattern:
                if match in triplet:
                    from_pattern.append(match)
            if len(from_pattern) == 3:
                for star in pattern:
                    if star not in from_pattern:
                        return star

    def _identify_stars_pattern(self, stars, triplets, commons, pattern):
        """Identify stars when a pattern is found."""
        star1, star2, star3, star4 = stars
        triplets1, triplets2, triplets3 = triplets
        common1_2, common1_3 = commons

        # We can identify 4 stars
        if len(common1_2) > 0 and len(common1_3) > 0:
            id_star1 = self._get_missing_star_from_triplets(triplets3, pattern)
            id_star3 = self._get_missing_star_from_triplets(triplets2, pattern)
            id_star4 = self._get_missing_star_from_triplets(triplets1, pattern)
            id_star2 = self._get_missing_star_from_triplets([[id_star1,
                                                              id_star3,
                                                              id_star4]],
                                                            pattern)
            for found_id, star in zip(
                        [id_star1, id_star2, id_star3, id_star4],
                        [star1, star2, star3, star4]):
                if found_id is not None:
                    star.set_real_star(self.get_star_by_id(found_id.real_star.hip_number))
                    star.set_identified(True)

        # We can identify only star3 and star4
        if len(common1_3) == 0:
            id_star3 = self._get_missing_star_from_triplets(triplets2, pattern)
            id_star4 = self._get_missing_star_from_triplets(triplets1, pattern)
            for found_id, star in zip([id_star3, id_star4], [star3, star4]):
                if found_id is not None:
                    star.set_real_star(self.get_star_by_id(found_id.real_star.hip_number))
                    star.set_identified(True)

    def find_stars_pattern(self, stars, err):
        """4 stars are needed"""
        pattern = []
        star1, star2, star3, star4 = stars
        c_err = 0.003
        while c_err < err:
            # Get triplets in abc
            triplets1 = self._get_triplets([star1, star2, star3], err=c_err)
            # Get triplets in abd
            triplets2 = self._get_triplets([star1, star2, star4], err=c_err)
            # Get triplets in triangle bcd
            triplets3 = self._get_triplets([star2, star3, star4], err=c_err)

            # Get commons triplets
            common1_2 = self._get_common_triplets(triplets1, triplets2)
            common1_3 = self._get_common_triplets(triplets1, triplets3)
            pattern = self._get_common_quads([common1_2, common1_3])

            # If There is only one match, we got the solution
            if len(pattern) == 1:
                self._identify_stars_pattern([star1, star2, star3, star4],
                                             [triplets1, triplets2, triplets3],
                                             [common1_2, common1_3], pattern[0])
                return [[star1, star2, star3, star4], pattern[0]]

            c_err += 0.001

        # No solution found
        print("No Solution Found!")
        return []

    @classmethod
    def _get_not_matched(cls, triplet, pair):
        unmatched = None
        for i in triplet:
            if i not in pair:
                unmatched = i

        return unmatched
