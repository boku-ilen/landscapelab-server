import fiona
import png
import webmercator
import numpy as np
from django.conf import settings
from django.contrib.gis.geos import Polygon, Point
import rasterio  # TODO: decide if we want to read raster or polygon data
from django.contrib.gis.utils import LayerMapping
from django.db.models import Avg

from raster.models import DigitalHeightModel, Tile
from landscapelab import utils
import logging

DEFAULT_DHM_FILE = settings.STATICFILES_DIRS[0] + "/raster/dhm_lamb_10m.tif"
DHM_SPLAT_FILE = settings.STATICFILES_DIRS[0] + "/raster/{}/{}/{}/{}.png"
DHM_SPLAT_IDENTIFIER = "dhm_splat"
DEFAULT_DHM_SRID = 3857  # WebMercator Aux Sphere
TILE_SIZE_PIXEL = 256

logger = logging.getLogger(__name__)


# imports the dhm into the postgis database
# FIXME: dummy -> we have to figure out input variables
def import_dhm(dhm_filename: str, bounding_box: Polygon, srid=DEFAULT_DHM_SRID):

    # delete all old data within the bounding box
    if bounding_box:
        logger.debug("delete all data from database within geometry {}".format(bounding_box))
        DigitalHeightModel.objects.filter(point__within=bounding_box).delete()

    # getting the type of dhm and check if we import a vector (*.shp) or raster file (anything else)
    if dhm_filename.lower().endswith(".shp"):

        # vector implementation
        logger.debug("staring vector import")
        mapping = {'height': 'float',
                   'point': 'POINT', }
        lm = LayerMapping(DigitalHeightModel, dhm_filename, mapping)
        lm.save(verbose=True)  # save the data to the database

    # raster implementation
    else:
        with rasterio.open(dhm_filename) as dhm_datasource:
            crs = dhm_datasource.get_crs()
            np_heightmap = dhm_datasource.read(1)  # we assume there is a single height band
            rows, cols = np_heightmap.shape
            logger.debug("starting raster import with {} points".format(rows * cols))

            count = 0
            for x in range(0, rows):
                for y in range(0, cols):
                    x_m, y_m = dhm_datasource.affine * (x, y)
                    point = Point(x_m, y_m, srid=crs)  # convert x,y to meters in crs
                    if count % 1000:
                        logger.debug("imported {} from {} ({} %)".format(count, rows * cols, count * 100 / rows * cols))
                    count += 1

                    # only import points within the bounding polygon
                    if bounding_box:
                        if not bounding_box.contains(point):
                            continue
                    dhm_point = DigitalHeightModel()
                    dhm_point.point = point
                    dhm_point.height = np_heightmap[x, y]
                    dhm_point.save()


# TODO: maybe move this to another file?
# gets the tile if it exists or initializes the requested tile
def get_or_initialize_tile(x: int, y: int, zoom: int):
    tile = Tile.objects.filter(x=x, y=y, lod=zoom)
    if not tile:
        tile = Tile()
        tile.x = x
        tile.y = y
        tile.lod = zoom
        tile.save()
    return tile


# generates the database (cache) entry for the dhm
def generate_dhm_db(x: int, y: int, zoom: int):

    # create the empty dhm array for this tile with an unsigned integer with 20 bit precision
    np_heightmap = np.zeros((TILE_SIZE_PIXEL, TILE_SIZE_PIXEL), dtype=np.uint32)

    # iterate to all pixels of the image in terms of projected coordinates
    point = webmercator.Point(tile_x=x, tile_y=y, zoom_level=zoom)
    meters_x_steps = np.arange(point.meter_x, point.meters_per_tile + point.meter_x, point.meters_per_pixel)
    meters_y_steps = np.arange(point.meter_y, point.meters_per_tile + point.meter_y, point.meters_per_pixel)
    pixel_x, pixel_y = -1, -1
    for m_x_from, m_x_to in utils.lookahead(meters_x_steps):
        pixel_x += 1
        for m_y_from, m_y_to in utils.lookahead(meters_y_steps):
            pixel_y += 1

            # don't calculate if we are beyond the last pixel
            if m_x_to is None or m_y_to is None:
                continue

            # get the available height information of the requested pixel
            bbox = Polygon.from_bbox((m_x_from, m_y_from, m_x_to, m_y_to))
            dhm_points = DigitalHeightModel.objects.filter(poly__contained=bbox)

            # if there are registered heights we have to calculate the average
            if dhm_points:
                np_heightmap[pixel_x, pixel_y] = dhm_points.aggregate(Avg('height'))
            # FIXME: we have to somehow estimate from the surounding values
            else:
                pass

    # store the result as cache of the tile in the database
    tile = get_or_initialize_tile(x, y, zoom)
    tile.heightmap = np_heightmap
    tile.save()

    return np_heightmap


# generates a single tile from dhm and splat information in the database
def generate_dhm_splat_tile(x: int, y: int, zoom: int):

    # load associated tile entry from db
    tile = get_or_initialize_tile(x, y, zoom)

    # load or generate dhm information
    np_dhm = tile.heightmap
    if not np_dhm:
        # generate tile in db
        np_dhm = generate_dhm_db(x, y, zoom)

    # create empty image
    np_image = np.zeros((TILE_SIZE_PIXEL, TILE_SIZE_PIXEL, 4), dtype=np.uint16)

    # add heightmap to the image
    # we expect values in centimeters as unsigned integer with values from 0-8500000
    # which requires 20bit to store. In the 16-bit per channel image this requires
    # 1,5 channels so we store it in RRGgbbaa
    pass  # FIXME: maybe it is currently sufficient to use two complete channels (RRGG)

    # TODO: we aggregate all height differences here and provide the final height profile
    # TODO: to the client. If this is not feasable due to performance issues, we go back
    # TODO: to the proposed solution to transfer the height deltas separably

    # TODO: we probably will work with numpy packbits and unpackbits

    # write the file including the alpha mask
    output_file = DHM_SPLAT_FILE.format(DHM_SPLAT_IDENTIFIER, zoom, y, x)
    png.from_array(np_image, 'RGBA').save(output_file)


# get the filename for the dhm and splatmap combined file from coordinates
# checks if the file exists or starts the calculation of given file
def get_dhmsplat_from_coords(tile_x, tile_y, zoom):
    filename = DHM_SPLAT_FILE.format(DHM_SPLAT_IDENTIFIER, zoom, tile_y, tile_x)
    if not os.path.isfile(filename):
        # TODO: maybe postpone the fetching (non-blocking) if not in debug?
        generate_dhm_splat_tile(tile_x, tile_y, zoom)
    return filename
