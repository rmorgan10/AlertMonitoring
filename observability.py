# functions to calculate observability metrics

import ephem
import numpy as np

import utils

class Event:

    def __init__(self, ra, dec, search_time=None, eventid=None, tag=None,
                 sun_alt_threshold=-14., moon_avoidance=False, save=False, plot=False):
        """
        ra and dec in degrees
        eventid is
        later in ephem Date format
        """

        self.ra = ra
        self.dec = dec
        equatorial_target = ephem.Equatorial(np.radians(self.ra), np.radians(self.dec))
        self.glon = np.degrees(ephem.Galactic(equatorial_target).lon)
        self.glat = np.degrees(ephem.Galactic(equatorial_target).lat)

        self.eventid = eventid
        self.tag = tag

        if search_time is None:
            self.search_time = ephem.now()
        else:
            self.search_time = ephem.Date(search_time)

        self.sun_alt_threshold = sun_alt_threshold

        self.observatory = utils.ctio()
        self.observatory.date = self.search_time

        if save:
            outfile_airmass = 'png'
            outfile_skymap = 'png'
            outfile_ortho = 'png'
            outfile_diagnostics = 'txt'
        else:
            outfile_airmass = None
            outfile_skymap = None
            outfile_ortho = None
            outfile_diagnostics = None

        self.optimal_time(search_interval=1., plot=plot, outfile=outfile_airmass, moon_avoidance=moon_avoidance)
        self.skymap(outfile=outfile_skymap)
        self.diagnostics(outfile=outfile_diagnostics)
        self.make_json()
        return

    def optimalTime(self, search_interval=1., plot=True, outfile=None, moon_avoidance=False):
        """
        Search interval in days
        """
        
        time_shift_array = np.linspace(0., search_interval, 10000)

        airmass_array = np.empty(len(time_shift_array))
        sun_alt_array = np.empty(len(time_shift_array))
        moon_alt_array = np.empty(len(time_shift_array))
        for ii, time_shift in enumerate(time_shift_array):
            date = ephem.Date(self.search_time + time_shift)
            self.observatory.date = ephem.Date(date)
        
            # Check if nighttime!
            sun_alt_array[ii] = np.degrees(ephem.Sun(self.observatory).alt)
            moon_alt_array[ii] = np.degrees(ephem.Moon(self.observatory).alt)

            ra_zenith, dec_zenith = self.observatory.radec_of(0, '90') # RA and Dec of zenith
            ra_zenith = np.degrees(ra_zenith)
            dec_zenith = np.degrees(dec_zenith)
            airmass_array[ii] = utils.getAirmass(ra_zenith, dec_zenith, self.ra, self.dec)
        
        self.observatory.date = self.search_time

        # Optimal time
        if not moon_avoidance:
            cut = (sun_alt_array < self.sun_alt_threshold)
        else:
            cut = (sun_alt_array < self.sun_alt_threshold) & (moon_alt_array < 0.)
        self.minimum_airmass = np.min(airmass_array[cut])
        optimal_time_shift = time_shift_array[cut][np.argmin(airmass_array[cut])]
        self.optimal_time = ephem.Date(self.search_time + optimal_time_shift)

        return

    def diagnostics(self, outfile=None):
        
        self.observatory.date = self.search_time

        sun = ephem.Sun(self.optimal_time)
        ra_sun, dec_sun = np.degrees(sun.ra), np.degrees(sun.dec)
        moon = ephem.Moon(self.optimal_time)
        ra_moon, dec_moon = np.degrees(moon.ra), np.degrees(moon.dec)
        sfd = utils.openEBVMap()
        nside = healpy.npix2nside(len(sfd))

        lines = ['Event',
                 '  Event ID = %s'%(self.eventid),
                 '  (ra, dec) = (%.4f, %.4f)'%(self.ra, self.dec),
                 'Date',
                 '  Now = %s (UTC)'%(ephem.now().__str__()),
                 '  Search time = %s (UTC)'%(self.search_time.__str__()),
                 '  Optimal time = %s (UTC)'%(self.optimal_time.__str__()),
                 '  Airmass at optimal time = %.2f'%(self.minimum_airmass),
                 'Sun',
                 '  Angular separation = %.2f (deg)'%(utils.angsep(self.ra, self.dec, ra_sun, dec_sun)),    
                 '  Next rising = %s (UTC)'%(self.observatory.next_rising(ephem.Sun()).__str__()),
                 '  Next setting = %s (UTC)'%(self.observatory.next_setting(ephem.Sun()).__str__()),
                 'Moon',
                 '  Illumination = %.2f'%(moon.moon_phase),
                 '  Angular separation = %.2f (deg)'%(utils.angsep(self.ra, self.dec, ra_moon, dec_moon)),
                 '  Next rising = %s (UTC)'%(self.observatory.next_rising(ephem.Moon()).__str__()),
                 '  Next setting = %s (UTC)'%(self.observatory.next_setting(ephem.Moon()).__str__()),
                 '  Next new moon = %s (UTC)'%(ephem.next_new_moon(ephem.now()).__str__()),
                 '  Next full moon = %s (UTC)'%(ephem.next_full_moon(ephem.now()).__str__()),
                 'Galactic',
                 '  (l, b) = (%.4f, %.4f)'%(self.glon, self.glat),
                 '  E(B-V) = %.2f'%(sfd[utils.angToPix(nside, self.glon, self.glat)])]

        if outfile:
            outfile = 'output/icecube_%s_diagnostics_%s.%s'%(self.eventid, utils.datestring(self.optimal_time), outfile)
            writer = open(outfile, 'w')
            for line in lines:
                writer.write(line + '\n')
            writer.close()

        return
    

    def make_json(self):
        outfile = 'output/icecube_%s_%s.json'%(self.eventid,
                                               utils.datestring(self.optimal_time))
        sispi = icecube_json.makeJson(self.ra, self.dec, self.eventid, self.optimal_time)
        icecube_json.writeJson(outfile, sispi)
