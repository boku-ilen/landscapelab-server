import logging
import os
import pickle

from django.http import Http404

from django.conf import settings
from vegetation.process_land_use import land_use_to_splatmap

SPLATMAP_BASE = settings.STATICFILES_DIRS[0] + "/phytocoenosis-splatmap/"
SPLATMAP_METER_Y = os.path.join(SPLATMAP_BASE, "{}")
SPLATMAP_PATH = os.path.join(SPLATMAP_METER_Y, "{}.png")
SPLATMAP_IDS_PATH = os.path.join(SPLATMAP_METER_Y, "{}.ids")

LAND_USE_BASE = settings.STATICFILES_DIRS[0] + "/raster/land-use/"
LAND_USE_METER_Y = os.path.join(LAND_USE_BASE, "{}")
LAND_USE_PATH = os.path.join(LAND_USE_METER_Y, "{}.png")


def get_splatmap_path_and_ids_for_coordinates(meter_x: int, meter_y: int):
    """Returns the filename of the splatmap for given x and y coordinates (in meters) and a list with all phytocoenosis
    IDs in this splatmap.
    If the splatmap doesn't exist yet, it is created.
    """

    # TODO: We need to decide on a grid and translate the meter coordinates to this grid, this current method is
    #  assuming that every meter has its own file!
    splat_filename = SPLATMAP_PATH.format(meter_y, meter_x)
    ids_filename = SPLATMAP_IDS_PATH.format(meter_y, meter_x)

    if not os.path.isfile(splat_filename):
        logging.info("Generating splatmap for {}...".format(splat_filename))
        create_splatmap(meter_x, meter_y)

    with open(ids_filename, 'rb') as idfile:
        ids = pickle.load(idfile)

    return splat_filename, ids


def create_splatmap(meter_x: int, meter_y: int):
    """Generates the phytocoenosis ID splatmap from the land use map at given x and y coordinates (in meters).

    Saves 2 files: The splatmap with phytocoenosis IDs and the pickle-serialized list of IDs in that splatmap.

    If the required sub-directories do not exist yet, they are created.
    If there is no appropriate land use map to use, Error 404 is thrown.
    """

    splatmap_filename = SPLATMAP_PATH.format(meter_y, meter_x)
    ids_filename = SPLATMAP_IDS_PATH.format(meter_y, meter_x)
    land_use_filename = LAND_USE_PATH.format(meter_y, meter_x)

    # If the land use file does not exist, raise a 404 error, since we can't construct a proper response then
    if not os.path.isfile(land_use_filename):
        raise Http404

    # Create all required directories if they don't yet exist
    meter_y = SPLATMAP_METER_Y.format(meter_y)

    if not (os.path.exists(SPLATMAP_BASE)):
        os.mkdir(SPLATMAP_BASE)

    if not (os.path.exists(meter_y)):
        os.mkdir(meter_y)

    splatmap, ids = land_use_to_splatmap(land_use_filename)
    splatmap.save(splatmap_filename)

    # Write used IDs to a file
    with open(ids_filename, 'wb+') as idfile:
        pickle.dump(list(ids), idfile)
