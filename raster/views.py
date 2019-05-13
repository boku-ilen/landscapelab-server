import webmercator
from django.http import JsonResponse

from landscapelab import utils
from raster import process_maps
from raster import png_to_response

from raster import tiles


# FIXME: remove hardcoded reference to specific region in path
DHM_BASE = "/raster/heightmap-region-nockberge"
ORTHO_BASE = "/raster/bmaporthofoto30cm"

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

    # answer with a json
    ret = {
        'ortho': utils.get_full_texture_path(filename_ortho),
        'map': filename_map,
        'dhm': utils.get_full_texture_path(filename_dhm)
    }
    return JsonResponse(ret)
