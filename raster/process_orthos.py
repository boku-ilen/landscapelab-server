import logging
import os
from pathlib import Path

from django.contrib.gis.geos import Polygon
from django.conf import settings
from requests import HTTPError

import webmercator
import owslib.wmts as wmts

# current default is the austrian basemap  TODO: make it configurable
DEFAULT_URL = "https://www.basemap.at/wmts/1.0.0/WMTSCapabilities.xml"
DEFAULT_LAYER = "bmaporthofoto30cm"
DEFAULT_ORTHO_SRID = {'init': 'EPSG:3857'}  # WebMercator Aux Sphere

# the format and location of the ortho pictures
ORTHOS_FILE = settings.STATICFILES_DIRS[0] + "/raster/{}/{}/{}/{}.jpeg"

logger = logging.getLogger(__name__)


# method to fetch a complete pyramid within a given bounding box
def fetch_wmts_tiles(bounding_box: Polygon, url=DEFAULT_URL, layer=DEFAULT_LAYER):

    # initialize wmts connection
    tile_server = wmts.WebMapTileService(url)

    # calculate possible extent
    if tile_server.contents[layer]:
        long1, lat1, long2, lat2 = tile_server.contents[layer].boundingBoxWGS84
        p1 = webmercator.Point(latitude=lat1, longitude=long1)
        p2 = webmercator.Point(latitude=lat2, longitude=long2)
        server_box = Polygon(((p1.meter_x, p1.meter_y),
                              (p1.meter_x, p2.meter_y),
                              (p2.meter_x, p2.meter_y),
                              (p2.meter_x, p1.meter_y),
                              (p1.meter_x, p1.meter_y)))
        unified_bb = server_box
        if bounding_box is not None:
            unified_bb = server_box.intersection(bounding_box)

        min_x, min_y = unified_bb.centroid
        max_x, max_y = min_x, min_y
        for x, y in unified_bb.coords[0]:  # first of multiple geometries hold the bb
            if x < min_x:
                min_x = x
            if x > max_x:
                max_x = x
            if y < min_y:
                min_y = y
            if y > max_y:
                max_y = y

        # get all tiles in the available extent and zoomlevel
        for zoom in range(15, 21):  # FIXME: fixed values -> configurable
            p_from = webmercator.Point(meter_x=min_x, meter_y=min_y, zoom_level=zoom)
            p_to = webmercator.Point(meter_x=max_x, meter_y=max_y, zoom_level=zoom)

            logger.info("getting all tiles with z {} for ({}, {}), ({}, {})".format(zoom, p_from.tile_x, p_from.tile_y,
                                                                                    p_to.tile_x, p_to.tile_y))
            for y in range(p_to.tile_y, p_from.tile_y+1):
                for x in range(p_from.tile_x, p_to.tile_x+1):
                    retry = True
                    while retry:
                        try:
                            fetch_wmts_tile(tile_server, layer, x, y, zoom)
                            retry = False
                        except Exception as e:
                            logger.warning("Got exception {} - need to repeat".format(e))
    else:
        pass  # TODO: error


# this fetches a single tile and put's it into our source directory
def fetch_wmts_tile(tile_server, layer, col, row, zoom):

    file = ORTHOS_FILE.format(layer, zoom, col, row)
    # create necessary subdirectories
    if not Path(file).is_file():
        try:
            os.makedirs(Path(file).parent)
        except FileExistsError:
            pass  # skip if all paths are already there
        logger.debug("getting tile {} {}/{}-{}".format(layer, zoom, col, row))
        try:
            tile = tile_server.gettile(layer=layer, tilematrix=str(zoom), row=row, column=col)
            out = open(file, 'wb')
            out.write(tile.read())
            out.close()

        except HTTPError:
            logger.warning("could not fetch tile for {} {}/{}-{}".format(layer, zoom, col, row))
    else:
        logger.debug("skipped tile {} {}/{}-{}".format(layer, zoom, col, row))


# get the filename based on tiles with the given coordinates
# TODO: maybe generalize to also be usable for the dhm png?
def filename_from_coords(layer: str, x_meter: float, y_meter: float, lod: int):

    p = webmercator.Point(meter_x=x_meter, meter_y=y_meter, zoom_level=lod)
    filename = ORTHOS_FILE.format(layer, lod, p.tile_y, p.tile_x)

    return filename
