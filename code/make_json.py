# generate observing scripts 

from collections import OrderedDict as odict
import copy
import json

import numpy as np

def create_obs(event, alert, prop_id, bands=['g', 'r', 'i'], dithers=2, exposures=1, exptime=150):
    
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
                tag = "DESNU: IceCube event %s: %i of %i"%(seqid, seqnum, seqtot)

                sispi_dict["RA"]      = alert.ra + (index_dither * (1. / 60.) / np.cos(np.radians(alert.dec)))
                sispi_dict["dec"]     = alert.dec + (index_dither * (1. / 60.))
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

    with open(outfile, 'wb') as out:
        out.write(json.dumps(data, **kwargs))

    return


def read_json(filename, **kwargs):
    with open(filename, 'r') as f:
        return json.loads(f.read(), **kwargs)


def choose_bands(event):
    return
