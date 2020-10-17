# Functions for generating plots

import ephem
import healpy
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.patches import Circle, Rectangle
import scipy.ndimage

import decam
import utils

def plot_forecast(event):
    airmasses, sun_seps, moon_seps, moon_illums = event.forecast()

    fig = plt.figure(figsize=(15, 5))
    ax = fig.add_subplot(111)

    cmap = cm.get_cmap('RdYlGn_r')

    # airmass
    base = np.arange(len(airmasses))
    for idx, airmass in enumerate(airmasses[0:-1]):
        ax.axvspan(base[idx], base[idx+1], color=cmap(airmass - 1.0), alpha=0.3)
        if idx % 2 == 0:
            if airmass < 5.0:
                ax.text(base[idx], max(max(moon_seps), max(sun_seps)) + 10, '%.2f' %airmass)

    # sun
    ax.plot(base, sun_seps, color='black', lw=0.5, label=None)
    ax.scatter(base, sun_seps, marker='o', s=300, facecolor='gold', edgecolor='black', zorder=5)

    # moon
    ax.plot(base, moon_seps, lw=0.5, color='black', label=None)
    ax.scatter(base, moon_seps, marker='o', s=500, facecolor='lightgray', edgecolor='black', zorder=5)
    for idx, moon_illum in enumerate(moon_illums):
        ax.text(base[idx], moon_seps[idx], str(int(moon_illum * 100)), 
                horizontalalignment='center', verticalalignment='center', zorder=10, fontsize=10)

    # plot params
    ax.tick_params(axis='x', labelsize=14)
    ax.tick_params(axis='y', labelsize=14)
    ax.set_xlim(-0.5, 30.5)
    ax.set_ylim(0, max(max(moon_seps), max(sun_seps)) + 20)
    ax.set_xlabel("Time Since IceCube Alert [days]", fontsize=16)
    ax.set_ylabel("Angular Separation [degrees]", fontsize=16)
    fig.tight_layout()
    
    return fig, ax

def plot_airmass(event):
    
    fig = plt.figure(figsize=(5, 5))
    ax = fig.add_subplot(111)
    
    #airmass
    ax.plot(event.time_shift_array, event.airmass_array, color='black', lw=3, label=None)
    
    # backgrounds
    labels, n = scipy.ndimage.label(event.sun_alt_array > event.sun_alt_threshold)
    for index in range(1, n + 1):
        time_shift_select = event.time_shift_array[labels == index]
        name = 'Daytime' if index == 1 else None
        ax.axvspan(np.min(time_shift_select), np.max(time_shift_select), color='red', alpha=0.15, zorder=-1, label=name)

    labels, n = scipy.ndimage.label((event.sun_alt_array < event.sun_alt_threshold) & (event.moon_alt_array > 0.))
    for index in range(1, n + 1):
        time_shift_select = event.time_shift_array[labels == index]
        name = 'Moony' if index == 1 else None
        ax.axvspan(np.min(time_shift_select), np.max(time_shift_select), color='yellow', alpha=0.15, zorder=-1, label=name)

    labels, n = scipy.ndimage.label((event.sun_alt_array < event.sun_alt_threshold) & (event.moon_alt_array < 0.))
    for index in range(1, n + 1):
        time_shift_select = event.time_shift_array[labels == index]
        name = 'Nighttime' if index == 1 else None
        ax.axvspan(np.min(time_shift_select), np.max(time_shift_select), color='green', alpha=0.15, zorder=-1, label=name)
        
    # optimal times
    ax.axvline(event.optimal_time - event.search_time, c='black', ls='--')
    ax.axhline(event.minimum_airmass, c='black', ls='--')
    
    # plot params
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(1.0, 2.1)
    ax.set_xlabel('Time Since Alert [days]', fontsize=16)
    ax.set_ylabel('Airmass', fontsize=16)
    ax.tick_params(axis='x', labelsize=14)
    ax.tick_params(axis='y', labelsize=14)
    ax.legend(fontsize=18)
    fig.tight_layout()
    
    return fig, ax


def plot_fov(event, alert):
    
    fig = plt.figure(figsize=(5, 5))
    ax = fig.add_subplot(111)
    
    # IceCube stuff
    circles = {'circ50': Circle((alert.ra, alert.dec), radius=alert.err50/60.0,
                                edgecolor='None', lw=3, facecolor='gray', alpha=0.2),
               'circ90': Circle((alert.ra, alert.dec), radius=alert.err90/60.0,
                                edgecolor='None', lw=3, facecolor='gray', alpha=0.2),
               'circ50_border': Circle((alert.ra, alert.dec), radius=alert.err50/60.0, 
                                       edgecolor='crimson', lw=3, facecolor='None'),
               'circ90_border': Circle((alert.ra, alert.dec), radius=alert.err90/60.0, 
                                       edgecolor='crimson', lw=3, facecolor='None', ls='--')}
    ax.add_patch(circles['circ50'])
    ax.add_patch(circles['circ90'])
    ax.add_patch(circles['circ50_border'])
    ax.add_patch(circles['circ90_border'])
    ax.scatter(alert.ra, alert.dec, marker='x', color='crimson', s=90, zorder=20)

    # DECam
    if event.observatory.name == 'CTIO':
        
        decam_boundaries = decam.get_centered_deg_fov(alert.ra, alert.dec)
        for ccd, coords in decam_boundaries.items():
            x = [k[0] for k in coords]
            y = [k[1] for k in coords]
            ax.plot(x, y, color='0.3')
        ax.set_title("Blanco / DECam", fontsize=16)
    
    elif event.observatory.name == 'KPNO':
        width, height = 40.0 / 60.0, 48.0 / 60.0 # 40' x 48'
        right_pointing = Rectangle((alert.ra, alert.dec - 0.5*height), 
                                   width, height, fill=False, color='0.3', zorder=20, lw=2)
        left_pointing = Rectangle((alert.ra - width, alert.dec - 0.5*height), 
                                  width, height, fill=False, color='0.3', zorder=20, lw=2)
        ax.add_patch(right_pointing)
        ax.add_patch(left_pointing)
        ax.set_title("WIYN / ODI", fontsize=16)
    
    else:
        raise NotImplementedError("Only CTIO and KPNO are allowed observatories.")
    
    # plot params
    for ax in axs:
        ax.set_xlabel("RA [degrees]", fontsize=16)
        ax.set_ylabel("Dec [degrees]", fontsize=16)
        ax.tick_params(axis='x', labelsize=14)
        ax.tick_params(axis='y', labelsize=14)
        ax.set_xlim(ax.get_xlim()[1], ax.get_xlim()[0])
    fig.tight_layout()    
    
    return fig, ax

def plot_skymap(event):
    color_des = 'blue'
    poly_des = utils.desPoly()
    sfd = utils.openEBVMap()
    title = '%s UTC'%(event.optimal_time.__str__())
    
    healpy.mollview(sfd, nest=True, coord=['G','C'], min=0., max=1., xsize=3000, cmap='binary', 
                    unit='E(B-V)', title=title)
    healpy.projplot(poly_des['ra'], poly_des['dec'], lonlat=True, c=color_des, lw=2)

    healpy.projscatter(event.ra, event.dec, lonlat=True, 
                       s=85, edgecolor='white', c='red', zorder=990, clip_on=False)

    sun = ephem.Sun(event.optimal_time)
    ra_sun, dec_sun = np.degrees(sun.ra), np.degrees(sun.dec)
    healpy.projscatter(ra_sun, dec_sun, lonlat=True, 
                       s=85, edgecolor='black', c='yellow', zorder=990, clip_on=False)

    moon = ephem.Moon(event.optimal_time)
    ra_moon, dec_moon = np.degrees(moon.ra), np.degrees(moon.dec)
    healpy.projscatter(ra_moon, dec_moon, lonlat=True, 
                       s=85, edgecolor='black', c='%.2f'%(moon.moon_phase), zorder=990, clip_on=False)

    fig = plt.gcf()
    ax = plt.gca()
    return fig, ax

def save(fig, event, alert, plot_type):
    event_dir = alert.name + '_' + str(alert.revision) + '/'
    fig.savefig(event_dir + event.observatory.name + '_' + plot_type + '.png')
    return

def make_plots(event, alert):
    # skymap
    fig, ax = plot_skymap(event)
    save(fig, event, alert, 'skymap')
    
    # forecast
    fig, ax = plot_forecast(event)
    save(fig, event, alert, 'forecast')
    
    # airmass
    fig, ax = plot_airmass(event)
    save(fig, event, alert, 'airmass')
    
    # fov
    fig, ax = plot_fov(event, alert)
    save(fig, event, alert, 'fov')
    
    return
    