import webmercator
from django.http import JsonResponse
from django.conf import settings

from raster import process_maps
from raster import png_to_response

from raster import tiles


# FIXME: remove hardcoded reference to specific region in path
DHM_BASE = settings.STATICFILES_DIRS[0] + "/raster/heightmap-region-nockberge"
ORTHO_BASE = settings.STATICFILES_DIRS[0] + "/raster/bmaporthofoto30cm"


# delivers a static raster file by given filename as json
# TODO: we will use this for textures and precalculated orthos?
def static_raster(request, filename):
    return JsonResponse(png_to_response.request_to_png_response(filename))


# returns the pointer to the filename which contains the combined ortho and dhm info
# TODO: maybe we want to provide the same API with given tile coordinates?
def get_ortho_dhm(request, meter_x: str, meter_y: str, zoom: str):

    # fetch the related filenames
    zoom = int(zoom)
    p = webmercator.Point(meter_x=float(meter_x), meter_y=float(meter_y), zoom_level=zoom)

    # TODO: The calls to process_orthos and calculate_dhm (in process_orthos.py) have been removed in favor
    #  of tiles.get_tile. This means that tiles are cropped, but never fetched from the internet.
    #  Should we check whether we can download the tile here, before cropping a lower LOD tile?
    filename_ortho = tiles.get_tile(float(meter_x), float(meter_y), zoom, ORTHO_BASE, False, "jpg")
    filename_map = process_maps.get_map_from_coords(p.tile_x, p.tile_y, zoom)
    filename_dhm = tiles.get_tile(float(meter_x), float(meter_y), zoom, DHM_BASE)

    # in debug mode make it possible to replace the path which is sent to
    # the server with another prefix to allow a remote access with different
    # path layout
    if settings.DEBUG and hasattr(settings, "CLIENT_PATH_PREFIX"):
        server_prefix = settings.STATICFILES_DIRS[0]
        client_prefix = settings.CLIENT_PATH_PREFIX
        filename_ortho = filename_ortho.replace(server_prefix, client_prefix)
        filename_dhm = filename_dhm.replace(server_prefix, client_prefix)
        filename_map = filename_map.replace(server_prefix, client_prefix)

    # answer with a json
    ret = {
        'ortho': filename_ortho,
        'map': filename_map,
        'dhm': filename_dhm
    }
    return JsonResponse(ret)
