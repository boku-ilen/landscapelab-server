import os
import webmercator
import logging
from PIL import Image
from raster import epx

ZOOM_PATH = "{}"
METER_X_PATH = os.path.join(ZOOM_PATH, "{}")
FULL_PATH = os.path.join(METER_X_PATH, "{}.png")

MAX_STEP_NUMBER = 10

logger = logging.getLogger(__name__)


def get_tile(meter_x: float, meter_y: float, zoom: int, path: str, do_epx_scale=False):
    """Returns the path to the tile at the given coordinates.

    The given path must lead to a tile directory. This means that the content of this directory must be organized like
    this:
    zoom level folders (containing) tile x folders (containing) tile y images

    If such a tile does not exist, it is created by cropping lower LOD tiles.
    """

    return get_cropped_recursively(meter_x, meter_y, zoom, path, 0, do_epx_scale)


def get_cropped_recursively(meter_x: float, meter_y: float, zoom: int, path: str, steps: int, do_epx_scale: bool):
    """Recursively crops tiles until the required one has been generated.

    To prevent a stack overflow, the steps are limited to MAX_STEP_NUMBER.
    """

    if steps >= MAX_STEP_NUMBER:
        return None

    full_path = os.path.join(path, FULL_PATH)

    this_point = webmercator.Point(meter_x=meter_x, meter_y=meter_y, zoom_level=zoom)
    this_point_filename = full_path.format(zoom, this_point.tile_x, this_point.tile_y)

    if not os.path.isfile(this_point_filename):
        prev_point = webmercator.Point(meter_x=meter_x, meter_y=meter_y, zoom_level=zoom - 1)
        prev_point_filename = full_path.format(zoom, prev_point.tile_x, prev_point.tile_y)

        if not os.path.isfile(prev_point_filename):
            get_cropped_recursively(meter_x, meter_y, zoom - 1, path, steps + 1, do_epx_scale)

        get_cropped_for_next_tile(meter_x, meter_y, zoom - 1, path, do_epx_scale)

    return this_point_filename


def get_cropped_for_next_tile(meter_x: float, meter_y: float, zoom: int, path: str, do_epx_scale: bool):
    """Takes the tile at the given parameters (which must exist!) and crops it to create a tile one zoom level above
    the given one. This new tile is then saved in the LOD pyramid.

    The quarter of the existing tile to crop to is chosen by utilizing how tile coordinates work in OSM:
    2x,2y    2x+1,2y
    2x,2y+1  2x+1,2y+1
    """

    p_wanted = webmercator.Point(meter_x=meter_x, meter_y=meter_y, zoom_level=zoom + 1)
    p_available = webmercator.Point(meter_x=meter_x, meter_y=meter_y, zoom_level=zoom)

    if p_wanted.tile_x % 2 == 0:
        left_right = [0, 0.5]
    else:
        left_right = [0.5, 1]

    if p_wanted.tile_y % 2 == 0:
        upper_lower = [0, 0.5]
    else:
        upper_lower = [0.5, 1]

    zoom_path_template = os.path.join(path, ZOOM_PATH)
    x_path_template = os.path.join(path, METER_X_PATH)
    full_path_template = os.path.join(path, FULL_PATH)

    available_filename = full_path_template.format(zoom, p_available.tile_x, p_available.tile_y)
    wanted_filename = full_path_template.format(zoom + 1, p_wanted.tile_x, p_wanted.tile_y)

    if not os.path.isfile(available_filename):
        logger.warning("get_cropped_for_next_tile requires a tile to exist at {}!".format(available_filename))
        return

    zoom_path = zoom_path_template.format(zoom + 1)
    if not os.path.isdir(zoom_path):
        os.mkdir(zoom_path)

    x_path = x_path_template.format(zoom + 1, p_wanted.tile_x)
    if not os.path.isdir(x_path):
        os.mkdir(x_path)

    available_image = Image.open(available_filename)
    available_size = tuple(available_image.size)

    wanted_image = available_image.crop((int(left_right[0] * available_size[0]),
                                         int(upper_lower[0] * available_size[1]),
                                         int(left_right[1] * available_size[0]),
                                         int(upper_lower[1] * available_size[1])))

    if do_epx_scale:
        wanted_image = epx.scale_epx(wanted_image)

    wanted_image.save(wanted_filename)
