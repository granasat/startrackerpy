from novas import compat as novas
from novas.compat import eph_manager

def main():
    jd_tt = novas.julian_date(2014, 8, 8, 10.5)
    mars = novas.make_object(0, 4, 'Mars', None)
    ra, dec, dis = novas.astro_planet(jd_tt, mars)
    print('R.A. %d:%02f' % (ra, abs(ra) % 1. * 60.))

if __name__ == "__main__":
    main()
