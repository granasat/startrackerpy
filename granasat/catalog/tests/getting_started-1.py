import numpy as np
import matplotlib.pyplot as plt
from astropy.stats import mad_std
from photutils import (datasets, DAOStarFinder, aperture_photometry,
                       CircularAperture)
hdu = datasets.load_star_image()
image = hdu.data[500:700, 500:700].astype(float)
image -= np.median(image)
bkg_sigma = mad_std(image)
daofind = DAOStarFinder(fwhm=4., threshold=3.*bkg_sigma)
sources = daofind(image)
positions = np.transpose((sources['xcentroid'], sources['ycentroid']))
apertures = CircularAperture(positions, r=4.)
phot_table = aperture_photometry(image, apertures)
brightest_source_id = phot_table['aperture_sum'].argmax()
plt.imshow(image, cmap='gray_r', origin='lower')
apertures.plot(color='blue', lw=1.5, alpha=0.5)
