import os

import fiona
import png
import webmercator
import numpy as np
from django.conf import settings
from django.contrib.gis.geos import Polygon, Point
import rasterio  # TODO: decide if we want to read raster or polygon data
from django.contrib.gis.utils import LayerMapping
from django.db.models import Avg

from raster.models import DigitalHeightModel
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
        logger.debug("starting raster import")
        with rasterio.open(dhm_filename) as dhm_datasource:
            crs = dhm_datasource.get_crs()
            transform = dhm_datasource.get_transform()
            np_heightmap = dhm_datasource.read(1)  # we assume there is a single height band
            rows, cols = np_heightmap.shape()

            for x in range(0, rows):
                for y in range(0, cols):
                    point = Point(transform * (x, y), srid=crs)  # convert x,y to meters in crs
                    if bounding_box.contains(point):  # only import points within the bounding polygon
                        dhm_point = DigitalHeightModel()
                        dhm_point.point = point
                        dhm_point.height = np_heightmap[x, y]
                        dhm_point.save()


# processes the imported height model and calculates a single tile
def process_dhm_to_tile(x: int, y: int, zoom: int):

    # iterate through the directory and for each file (maybe multithreaded)
    # calculate the coordinates of each pixel and fetch the according height
    # information and generate a numpy array
    # FIXME: do this in another function ?

    # create empty image
    np_image = np.zeros((TILE_SIZE_PIXEL, TILE_SIZE_PIXEL, 4), dtype=np.uint16)

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
                np_image[pixel_x, pixel_y] = dhm_points.aggregate(Avg('height'))
            # FIXME: we have to somehow estimate from the surounding values
            else:
                pass

    # write the file including the alpha mask
    output_file = DHM_SPLAT_FILE.format(DHM_SPLAT_IDENTIFIER, zoom, y, x)
    png.from_array(np_image, 'RGBA').save(output_file)


# get the filename for the dhm and splatmap combined file from coordinates
# checks if the file exists or starts the calculation of given file
def get_dhmsplat_from_coords(tile_x, tile_y, zoom):
    filename = DHM_SPLAT_FILE.format(DHM_SPLAT_IDENTIFIER, zoom, tile_y, tile_x)
    if not os.path.isfile(filename):
        # TODO: maybe postpone the fetching (non-blocking) if not in debug?
        process_dhm_to_tile(tile_x, tile_y, zoom)
    return filename
