import numpy as np
from astropy.io import fits
import healpy
import ephem

############################################################

def ctio():
    # http://www.ctio.noao.edu/noao/content/coordinates-observatories-cerro-tololo-and-cerro-pachon
    LON_CTIO = '-70:48:23.49'
    LAT_CTIO = '-30:10:10.78'
    ELEVATION_CTIO = 2206.8 # m

    observatory = ephem.Observer()
    observatory.lon = LON_CTIO
    observatory.lat = LAT_CTIO
    observatory.elevation = ELEVATION_CTIO
    return observatory

############################################################

def angsep(lon1,lat1,lon2,lat2):
    """
    Angular separation (deg) between two sky coordinates.
    Borrowed from astropy (www.astropy.org)

    Notes
    -----
    The angular separation is calculated using the Vincenty formula [1],
    which is slighly more complex and computationally expensive than
    some alternatives, but is stable at at all distances, including the
    poles and antipodes.

    [1] http://en.wikipedia.org/wiki/Great-circle_distance
    """
    lon1,lat1 = np.radians([lon1,lat1])
    lon2,lat2 = np.radians([lon2,lat2])
    
    sdlon = np.sin(lon2 - lon1)
    cdlon = np.cos(lon2 - lon1)
    slat1 = np.sin(lat1)
    slat2 = np.sin(lat2)
    clat1 = np.cos(lat1)
    clat2 = np.cos(lat2)

    num1 = clat2 * sdlon
    num2 = clat1 * slat2 - slat1 * clat2 * cdlon
    denominator = slat1 * slat2 + clat1 * clat2 * cdlon

    return np.degrees(np.arctan2(np.hypot(num1,num2), denominator))

############################################################

def getAirmass(lon_zenith, lat_zenith, lon, lat):
    """
    Safety handling when angular separation to zenith is more than 90 deg
    """
    airmass = 1. / np.cos(np.radians(angsep(lon, lat, lon_zenith, lat_zenith)))
    if np.isscalar(airmass):
        if airmass < 1.:
            airmass = 999.
    else:
        airmass[airmass < 1.] = 999.
    return airmass

############################################################

def openEBVMap(infile='data/lambda_sfd_ebv.fits', column='TEMPERATURE'):
    reader = fits.open(infile)
    m = reader[1].data[column]
    reader.close()
    return m

############################################################

def angToPix(nside, lon, lat):
    """
    Input (lon, lat) in degrees instead of (theta, phi) in radians
    """
    theta = np.radians(90. - lat)
    phi = np.radians(lon)
    return healpy.ang2pix(nside, theta, phi)

############################################################

def desPoly():
    infile = 'data/round13-poly.txt'
    data = np.genfromtxt(infile, names=['ra', 'dec'])
    return data

############################################################

def datestring(date):
    return date.__str__().replace('/','-').replace(' ','-').replace(':','-')

############################################################
