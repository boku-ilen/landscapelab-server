import webmercator
from django.http import JsonResponse

from landscapelab import utils
from raster import png_to_response, process_maps

from raster import tiles


# FIXME: remove hardcoded reference to specific region in path
DHM_BASE = "/raster/heightmap-region-nockberge"
ORTHO_BASE = "/raster/bmaporthofoto30cm"
MAP_BASE = "/raster/{}".format(process_maps.DEFAULT_LAYER)  # TODO: how to configure different map styles later on?


# delivers a static raster file by given filename as json
# TODO: we will use this for textures and precalculated orthos?
def static_raster(request, filename):
    return JsonResponse(png_to_response.request_to_png_response(filename))


# returns the pointer to the filename which contains the combined ortho and dhm info
def get_ortho_dhm(request, meter_x: str, meter_y: str, zoom: str):

    # fetch the related filenames
    zoom = int(zoom)
    meter_x = float(meter_x)
    meter_y = float(meter_y)

    # TODO: maybe we add callbacks later to generate the files if they could not be found
    filename_ortho = tiles.get_tile(meter_x, meter_y, zoom, ORTHO_BASE, False, "jpg")
    filename_map = tiles.get_tile(meter_x, meter_y, zoom, MAP_BASE, False, "jpg")
    filename_dhm = tiles.get_tile(meter_x, meter_y, zoom, DHM_BASE)

    # answer with a json
    ret = {
        'ortho': utils.get_full_texture_path(filename_ortho),
        'map': utils.get_full_texture_path(filename_map),
        'dhm': utils.get_full_texture_path(filename_dhm)
    }
    return JsonResponse(ret)
