import logging
import os

from django.http import Http404

import settings
from process_land_use import land_use_to_splatmap

SPLATMAP_BASE = settings.STATICFILES_DIRS[0] + "/phytocoenosis-splatmap/"
SPLATMAP_METER_Y = os.path.join(SPLATMAP_BASE, "{}")
SPLATMAP_PATH = os.path.join(SPLATMAP_METER_Y, "{}.png")

LAND_USE_BASE = settings.STATICFILES_DIRS[0] + "/raster/land-use/"
LAND_USE_METER_Y = os.path.join(LAND_USE_BASE, "{}")
LAND_USE_PATH = os.path.join(LAND_USE_METER_Y, "{}.png")


def get_splatmap_for_coordinates(meter_x: int, meter_y: int):
    """Returns the filename of the splatmap for given x and y coordinates (in meters).
    If the splatmap doesn't exist yet, it is created.
    """

    # TODO: We need to decide on a grid and translate the meter coordinates to this grid, this current method is
    #  assuming that every meter has its own file!
    filename = SPLATMAP_PATH.format(meter_y, meter_x)

    if not os.path.isfile(filename):
        logging.info("Generating splatmap for {}...".format(filename))
        create_splatmap(meter_x, meter_y)

    return filename


def create_splatmap(meter_x: int, meter_y: int):
    """Generates the splatmap from the land use map at given x and y coordinates (in meters).

    If there is no appropriate land use map to use, Error 404 is thrown.
    """

    splatmap_filename = SPLATMAP_PATH.format(meter_y, meter_x)
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

    splatmap = land_use_to_splatmap(land_use_filename)
    splatmap.save(splatmap_filename)
