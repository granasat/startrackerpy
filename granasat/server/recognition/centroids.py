#!/usr/bin/env python3


WIDTH = 1280
HEIGHT = 960

class Centroid:
    pass

class CentroidVector:
    pass


def centroiding(threshold1. threshold2, threshold3, ROI, image):
    vector_of_centroids = []

    limit = (ROI-1)/2
    for i in range(limit, HEIGHT-limit):
        for j in range(limit, WIDTH-limit):
            if image[i*WIDTH+j] >= threshold1:
                pass
            pass





def main():
    centroids = centroiding(threshold1. threshold2, threshold3, ROI, image_data)
