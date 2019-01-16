import fiona
import png
import numpy as np
from django.conf import settings
from django.contrib.gis.geos import Polygon, Point
import rasterio  # TODO: decide if we want to read raster or polygon data
from django.contrib.gis.utils import LayerMapping
from raster.models import DigitalHeightModel
import logging

DEFAULT_DHM_FILE = settings.STATICFILES_DIRS[0] + "/raster/dhm_lamb_10m.tif"
DHM_FILE = settings.STATICFILES_DIRS[0] + "/raster/{}/{}/{}/{}.png"
DEFAULT_DHM_SRID = 3857  # WebMercator Aux Sphere
TILE_SIZE_PIXEL = 256

logger = logging.getLogger(__name__)


# imports the dhm into the postgis database
# FIXME: dummy -> we have to figure out input variables
def import_dhm(dhm_filename: str, bounding_box: Polygon, srid=DEFAULT_DHM_SRID):

    # delete all old data within the bounding box
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

        # FIXME: use fiona if geos does not work
        #    with fiona.open(dhm_filename) as dhm_shapefile:
        #        for feature in dhm_shapefile:
        #            # TODO: what to do when the entry is already there?
        #            dhm_point = DigitalHeightModel()
        #            dhm_point.height = feature['properties'][]
        #
        #            dhm_point.point = Point(x, y, srid=srid)
        #            dhm_point.save()

    else:

        # raster implementation
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


# FIXME: we have to think about input variables
def process_dhm_to_tile(x: int, y: int, zoom: int):

    # iterate through the directory and for each file (maybe multithreaded)
    # calculate the coordinates of each pixel and fetch the according height
    # information and generate a numpy array

    # get the available height information of the requested extent


    # create empty image
    np_image = np.zeros((TILE_SIZE_PIXEL, TILE_SIZE_PIXEL, 4), dtype=np.uint16)

    # write the file including the alpha mask
    output_file = DHM_FILE.format("dhm", zoom, y, x)
    png.from_array(np_image, 'RGBA').save(output_file)
