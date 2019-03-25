import logging
import os

from PIL import Image
from django.conf import settings

LAND_USE_BASE = settings.STATICFILES_DIRS[0] + "/land-use/data"
LAND_USE_ZOOM = os.path.join(LAND_USE_BASE, "{}")
LAND_USE_METER_X = os.path.join(LAND_USE_ZOOM, "{}")
LAND_USE_PATH = os.path.join(LAND_USE_METER_X, "{}.png")


def convert_tms_osm_coordinates(tile_x: int, tile_y: int, zoom: int):
    """Converts the given tile coordinates between OSM and TMS format (OSM -> TSM or TSM -> OSM).

    tile_x and zoom stay the same, the only difference is in tile_y. This is because TMS places the first quad-tree
    tile at the bottom left, while the OSM/Google/Bing specification starts at the top left.
    """

    new_x = tile_x
    new_y = (1 << zoom) - tile_y - 1
    new_zoom = zoom

    return new_x, new_y, new_zoom


def get_splatmap_path_and_ids_for_coordinates(tile_x: int, tile_y: int, zoom: int):
    """Returns the filename of the splatmap for given x and y coordinates (in meters) and a list with all phytocoenosis
    IDs in this splatmap.
    If the splatmap doesn't exist yet, it is created.
    """
    
    tile_x, tile_y, zoom = convert_tms_osm_coordinates(tile_x, tile_y, zoom)

    splat_filename = LAND_USE_PATH.format(zoom, tile_x, tile_y)

    if not os.path.isfile(splat_filename):
        logging.info("No splatmap at {}!".format(splat_filename))
        return None, None

    return splat_filename, get_ids(splat_filename)


def get_ids(filename):
    """Returns a list with all IDs (that is, all pixel values) in a given splatmap."""

    id_list = list()

    if os.path.exists(filename):
        splatmap_image = Image.open(filename)
        id_list = list(set([pixel[0] for pixel in splatmap_image.getdata()]))  # Ignore alpha channel

    return id_list
