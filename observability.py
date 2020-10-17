# functions to calculate observability metrics

from datetime import timedelta

import ephem
import healpy
import numpy as np

import utils

class Event:

    def __init__(self, ra, dec, observatory, search_time=None, eventid=None, tag=None,
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

        self.observatory = observatory
        self.observatory.date = self.search_time

        self.optimal_time(search_interval=1., plot=plot, moon_avoidance=moon_avoidance)
        return

    def optimal_time(self, search_interval=1., plot=True, moon_avoidance=False):
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
        self.time_shift_array = time_shift_array
        self.airmass_array = airmass_array
        self.sun_alt_array = sun_alt_array
        self.moon_alt_array = moon_alt_array

        # Optimal time
        if not moon_avoidance:
            cut = (sun_alt_array < self.sun_alt_threshold)
        else:
            cut = (sun_alt_array < self.sun_alt_threshold) & (moon_alt_array < 0.)
        self.minimum_airmass = np.min(airmass_array[cut])
        optimal_time_shift = time_shift_array[cut][np.argmin(airmass_array[cut])]
        self.optimal_time = ephem.Date(self.search_time + optimal_time_shift)

        return

    def diagnostics(self, return_lines=True):
        # calculate metrics
        self.observatory.date = self.search_time
        sun = ephem.Sun(self.optimal_time)
        ra_sun, dec_sun = np.degrees(sun.ra), np.degrees(sun.dec)
        moon = ephem.Moon(self.optimal_time)
        ra_moon, dec_moon = np.degrees(moon.ra), np.degrees(moon.dec)
        sfd = utils.openEBVMap()
        nside = healpy.npix2nside(len(sfd))
        
        # store necessary properties
        self.sun_sep = utils.angsep(self.ra, self.dec, ra_sun, dec_sun)
        self.moon_sep = utils.angsep(self.ra, self.dec, ra_moon, dec_moon)
        self.moon_illum = moon.moon_phase

        # make report
        lines = ['Event',
                 '  Event ID = %s'%(self.eventid),
                 '  (ra, dec) = (%.4f, %.4f)'%(self.ra, self.dec),
                 'Date',
                 '  Now = %s (UTC)'%(ephem.now().__str__()),
                 '  Search time = %s (UTC)'%(self.search_time.__str__()),
                 '  Optimal time = %s (UTC)'%(self.optimal_time.__str__()),
                 '  Airmass at optimal time = %.2f'%(self.minimum_airmass),
                 'Sun',
                 '  Angular separation = %.2f (deg)'%(self.sun_sep),    
                 '  Next rising = %s (UTC)'%(self.observatory.next_rising(ephem.Sun()).__str__()),
                 '  Next setting = %s (UTC)'%(self.observatory.next_setting(ephem.Sun()).__str__()),
                 'Moon',
                 '  Illumination = %.2f'%(moon.moon_phase),
                 '  Angular separation = %.2f (deg)'%(self.moon_sep),
                 '  Next rising = %s (UTC)'%(self.observatory.next_rising(ephem.Moon()).__str__()),
                 '  Next setting = %s (UTC)'%(self.observatory.next_setting(ephem.Moon()).__str__()),
                 '  Next new moon = %s (UTC)'%(ephem.next_new_moon(ephem.now()).__str__()),
                 '  Next full moon = %s (UTC)'%(ephem.next_full_moon(ephem.now()).__str__()),
                 'Galactic',
                 '  (l, b) = (%.4f, %.4f)'%(self.glon, self.glat),
                 '  E(B-V) = %.2f'%(sfd[utils.angToPix(nside, self.glon, self.glat)])]
        
        if return_lines:
            return lines
        return
    

    #def make_json(self):
    #    outfile = 'output/icecube_%s_%s.json'%(self.eventid,
    #                                           utils.datestring(self.optimal_time))
    #    sispi = icecube_json.makeJson(self.ra, self.dec, self.eventid, self.optimal_time)
    #    icecube_json.writeJson(outfile, sispi)
    #    return

    def forecast(self):

        airmasses, sun_seps, moon_seps, moon_illums = [], [], [], []

        for day in range(31):
            search_time = self.search_time.datetime() + timedelta(days=day)
            new_event = Event(self.ra, self.dec, self.observatory, search_time=search_time)
            new_event.diagnostics(return_lines=False)

            airmasses.append(new_event.minimum_airmass)
            sun_seps.append(new_event.sun_sep)
            moon_seps.append(new_event.moon_sep)
            moon_illums.append(new_event.moon_illum)

        return airmasses, sun_seps, moon_seps, moon_illums
