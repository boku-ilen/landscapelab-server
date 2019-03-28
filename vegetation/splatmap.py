import logging
import os

import webmercator
from PIL import Image
from django.conf import settings

from raster.tiles import get_tile

LAND_USE_BASE = settings.STATICFILES_DIRS[0] + "/land-use/data"


def get_splatmap_path_and_ids_for_coordinates(meter_x: float, meter_y: float, zoom: int):
    """Returns the filename of the splatmap for given x and y coordinates (in meters) and a list with all phytocoenosis
    IDs in this splatmap.
    If the splatmap doesn't exist yet, it is created.
    """

    splat_filename = get_tile(meter_x, meter_y, zoom, LAND_USE_BASE)

    return splat_filename, get_ids(splat_filename)


def get_ids(filename):
    """Returns a list with all IDs (that is, all pixel values) in a given splatmap."""

    id_list = list()

    if os.path.exists(filename):
        splatmap_image = Image.open(filename)
        id_list = list(set([pixel[0] for pixel in splatmap_image.getdata()]))  # Ignore alpha channel

    return id_list



