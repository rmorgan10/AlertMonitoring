# generate observing scripts 

from collections import OrderedDict as odict
import copy
import json

import numpy as np

def create_obs(event, alert, prop_id, bands, dithers, exposures, exptime):
    
    sispi_dict_base = odict([
        ("filter",  None),
        ("program", "des nu"),
        ("seqtot",  None),
        ("seqnum",  None),
        ("expType", "object"),
        ("object",  None),
        ("comment", None),
        ("note",    "Added to queue from desnu json file, not obstac"),
        ("seqid",   None),
        ("RA",      None),
        ("propid",  prop_id), # like "2019A-0240"
        ("dec",     None),
        ("exptime", 150),
        ("wait",    "False")
    ])

    seqnum = 1
    seqtot = len(bands) * dithers * exposures
    seqid = alert.name

    sispi = []
    for band in bands:
        for idx_dither in range(dithers):
            for idx_exposure in range(exposures):

                sispi_dict = copy.deepcopy(sispi_dict_base)
                tag = "DESNU %s hex %i of %i"%(seqid, seqnum, seqtot)

                sispi_dict["RA"]      = alert.ra + (idx_dither * (1. / 60.) / np.cos(np.radians(alert.dec)))
                sispi_dict["dec"]     = alert.dec + (idx_dither * (1. / 60.))
                sispi_dict["filter"]  = band
                sispi_dict["seqnum"]  = seqnum
                sispi_dict["seqtot"]  = seqtot
                sispi_dict["object"]  = tag
                sispi_dict["comment"] = tag
                sispi_dict["seqid"]   = seqid

                sispi.append(sispi_dict)
                seqnum += 1

    return sispi


def write_json(outfile, data, **kwargs):
    kwargs.setdefault('indent', 4)
    json.encoder.FLOAT_REPR = lambda o: format(o, '.4f')

    with open(outfile, 'w+', encoding="utf8") as out:
        out.write(json.dumps(data, **kwargs))

    return


def read_json(filename, **kwargs):
    with open(filename, 'r') as f:
        return json.loads(f.read(), **kwargs)


def choose_bands(event):

    if not hasattr(event, 'moon_sep'):
        event.diagnostics(return_lines=False)

    moony = event.moon_sep < 60.0 or event.moon_illum > 0.4

    if event.observatory.name == 'CTIO':
        if moony:
            return ['r', 'i', 'z']
        else:
            return ['g', 'r', 'i']

    elif event.observatory.name == 'KPNO':
        return ["r'", "i'"]

    else:
        raise NotImplementedError("Only CTIO and KPNO are built into the JSON functions")

def load_propid(event):
    with open('PROPID.txt', 'r') as f:
        for line in f.readlines():
            if line[0] == '#':
                continue
                
            clean_line = line.strip()
            observatory = clean_line.split(':')[0].strip().upper()

            if observatory == event.observatory.name:
                propid = clean_line.split(':')[1].strip()
                return propid

        # If we get here, observaotry name was not found
        raise ValueError(f"{event.observatory.name} is not found in PROPID.txt")
        

def generate_script(event, alert, propid=None, bands=None, dithers=None, exposures=None, exptime=None, outfile=None):

    if bands is None:
        bands = choose_bands(event)

    if propid is None:
        propid = load_propid(event)

    if dithers is None:
        dithers = 2
    
    if exposures is None:
        exposures = 1

    if exptime is None:
        exptime = 150
        
    if outfile is None:
        outfile = '../' + alert.name + '_' + str(alert.revision) + '/' + event.observatory.name + '.json'

    json_data = create_obs(event, alert, propid, bands, dithers, exposures, exptime)
    write_json(outfile, json_data)

    return
