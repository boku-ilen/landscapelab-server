import os
import webmercator
import logging
from PIL import Image

from landscapelab import utils
from raster import epx
from django.contrib.gis.geos import Point
from location.models import Scenario
from assetpos.models import Tile

ZOOM_PATH = "{}"
METER_X_PATH = utils.join_path(ZOOM_PATH, "{}")
FULL_PATH = utils.join_path(METER_X_PATH, "{}.{}")

MAX_STEP_NUMBER = 8

logger = logging.getLogger(__name__)


# TODO: maybe add a callback to the parameters, which is called if the file could not
# TODO: be found and needs to be downloaded (or generated) externally
def get_tile(meter_x: float, meter_y: float, zoom: int, path: str, do_epx_scale=False, file_ending="png"):
    """Returns the path to the tile at the given coordinates.

    The given path must lead to a tile directory. This means that the content of this directory must be organized like
    this:
    zoom level folders (containing) tile x folders (containing) tile y images

    If such a tile does not exist, it is created by cropping lower LOD tiles.
    """

    return get_cropped_recursively(meter_x, meter_y, zoom, path, 0, do_epx_scale, file_ending)


def get_cropped_recursively(meter_x: float, meter_y: float, zoom: int, path: str, steps: int, do_epx_scale: bool, file_ending: str):
    """Recursively crops tiles until the required one has been generated.

    To prevent a stack overflow, the steps are limited to MAX_STEP_NUMBER.
    """

    if steps >= MAX_STEP_NUMBER:
        # No tile that could be cropped has been found for the set MAX_STEP_NUMBER
        logger.error("{}: No tile could be found or created (tried from zoom {} down to {}) at location {}, {}!"
                     " Possible causes: Missing data, wrong path, no write permissions"
                     .format(path, zoom + steps, zoom, meter_x, meter_y))
        return None

    full_path = utils.join_path(path, FULL_PATH)

    this_point = webmercator.Point(meter_x=meter_x, meter_y=meter_y, zoom_level=zoom)
    this_point_filename = full_path.format(zoom, this_point.tile_x, this_point.tile_y, file_ending)

    if not os.path.isfile(this_point_filename) or (os.path.getsize(this_point_filename) == 0):
        prev_point = webmercator.Point(meter_x=meter_x, meter_y=meter_y, zoom_level=zoom - 1)
        prev_point_filename = full_path.format(zoom, prev_point.tile_x, prev_point.tile_y, file_ending)

        if not os.path.isfile(prev_point_filename) or (os.path.getsize(prev_point_filename) == 0):
            get_cropped_recursively(meter_x, meter_y, zoom - 1, path, steps + 1, do_epx_scale, file_ending)

        get_cropped_for_next_tile(meter_x, meter_y, zoom - 1, path, do_epx_scale, file_ending)

    return this_point_filename


def get_cropped_for_next_tile(meter_x: float, meter_y: float, zoom: int, path: str, do_epx_scale: bool, file_ending: str):
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

    zoom_path_template = utils.join_path(path, ZOOM_PATH)
    x_path_template = utils.join_path(path, METER_X_PATH)
    full_path_template = utils.join_path(path, FULL_PATH)

    available_filename = full_path_template.format(zoom, p_available.tile_x, p_available.tile_y, file_ending)
    wanted_filename = full_path_template.format(zoom + 1, p_wanted.tile_x, p_wanted.tile_y, file_ending)

    if not os.path.isfile(available_filename):
        # Nothing here yet - we might recurse further in get_cropped_recursively
        return

    x_path = x_path_template.format(zoom + 1, p_wanted.tile_x)
    os.makedirs(x_path, exist_ok=True)

    try:
        available_image = Image.open(available_filename)

        # PIL needs the image to be in RGB mode for processing - convert it if necessary
        original_image_mode = available_image.mode
        if original_image_mode != "RGB":
            available_image.convert('RGB')

        available_size = tuple(available_image.size)

        wanted_image = available_image.crop((int(left_right[0] * available_size[0]),
                                             int(upper_lower[0] * available_size[1]),
                                             int(left_right[1] * available_size[0]),
                                             int(upper_lower[1] * available_size[1])))

        if do_epx_scale:
            wanted_image = epx.scale_epx(wanted_image)

        # If the image has been converted to RGB for processing, convert it back to the original mode
        if original_image_mode != wanted_image.mode:
            wanted_image.convert(original_image_mode)

        # FIXME: It is possible that in the time since we last checked whether the image exists,
        #  the same request was handled in another thread. This means that the image already
        #  exists at this point, even though we checked earlier. We need a Mutex!
        wanted_image.save(wanted_filename)

    except OSError:
        logger.warning("Could not process file {} - this file does not seem valid". format(available_filename))


# returns the highest LOD (or LOD = max_lod) tile that contains the specified location
# if the LOD is not high enough new tiles will be generated
# TODO binary search for the highest currently existing tile could significantly increase performance
def get_highest_lod_tile(location: Point, parent_tile: Tile, min_lod: int, max_lod: int = 28):

    # break recursion if LOD has reached
    # the specified max value
    if parent_tile.lod >= max_lod:
        return parent_tile

    # get x and y coordinate for the next lod and look for a matching tile
    x, y = get_corresponding_tile_coordinates(location, parent_tile.lod + 1)
    child_tile = Tile.objects.filter(x=x, y=y, lod=parent_tile.lod + 1)

    # if no matching tile could be found
    # check if the LOD is high enough
    if not child_tile:
        if parent_tile.lod >= min_lod:
            # return if LOD is high enough
            return parent_tile

        else:
            # create missing LODs if it is not high enough
            return generate_remaining_sub_tiles(parent_tile, location, min_lod)

    # continue recursion until the highest LOD tile is found
    return get_highest_lod_tile(location, child_tile.first(), min_lod, max_lod)


# recursively generates sub-tiles, from one specific tile with low LOD until
# the LOD hits the specified target_lod
# the last generated Tile will be returned
def generate_remaining_sub_tiles(parent_tile: Tile, location: Point, target_lod: int):

    # break recursion and return highest LOD tile if LOD is high enough
    if parent_tile.lod >= target_lod:
        return parent_tile

    # generate tile with higher LOD
    x, y = get_corresponding_tile_coordinates(location, parent_tile.lod + 1)
    child_tile = generate_sub_tile(x, y, parent_tile)

    # continue recursion until LOD is high enough
    return generate_remaining_sub_tiles(child_tile, location, target_lod)


# generates a child-tile of specified parent-tile
def generate_sub_tile(x, y, parent: Tile):
    child = Tile(scenario=parent.scenario, parent=parent, x=x, y=y, lod=parent.lod + 1)
    child.save()

    # TODO move assets that are in parent and child to child

    return child


# returns the root tile of specified scenario
def get_root_tile(scenario: Scenario):

    # return Tile.objects.get(scenario=scenario, parent='self') # this apparently does not work
    # TODO maybe find a more efficient solution (may be possible with simple statement like in comment above)

    # find tile with
    tiles = Tile.objects.filter(scenario=scenario, x=0, y=0, lod=0)
    for tile in tiles:
        if tile.pk == tile.parent.pk:
            return tile

    # create a new root tile if none could be found
    tile = Tile(scenario=scenario, x=0, y=0, lod=0)
    tile.save()
    tile.parent = tile
    tile.save()

    return tile


# returns the x and y coordinates of the tile that
# contains the specified location and has the specified LOD
def get_corresponding_tile_coordinates(location: Point, lod):

    coord = webmercator.Point(meter_x=location.x, meter_y=location.y, zoom_level=lod)
    return coord.tile_x, coord.tile_y
