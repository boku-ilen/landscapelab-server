import webmercator
from django.http import JsonResponse

from  django.conf import settings
from raster import calculate_dhm
from raster import process_orthos
from .png_to_response import *

# TODO: Remove once dhmsplat is finished
DHM_FILE = settings.STATICFILES_DIRS[0] + "/raster/heightmap.png"


# delivers a static raster file by given filename as json
# TODO: we will use this for textures and precalculated orthos?
def static_raster(request, filename):
    return JsonResponse(request_to_png_response(filename))


# returns the pointer to the filename which contains the combined ortho and dhm info
# TODO: maybe we want to provide the same API with given tile coordinates?
def get_ortho_dhm(request, meter_x: str, meter_y: str, zoom: str):

    # fetch the related filenames
    zoom = int(zoom)
    p = webmercator.Point(meter_x=float(meter_x), meter_y=float(meter_y), zoom_level=zoom)
    filename_ortho = process_orthos.get_ortho_from_coords(p.tile_x, p.tile_y, zoom)
    filename_dhmsplat = calculate_dhm.get_dhmsplat_from_coords(p.tile_x, p.tile_y, zoom)

    # TODO: Remove once dhmsplat is finished
    if zoom == 12:
        dhm = DHM_FILE
    else:
        dhm = 'None'

    # answer with a json
    ret = {
        'ortho': filename_ortho,
        'dhm': dhm,  # TODO: Remove once dhmsplat is finished
        'dhmsplat': filename_dhmsplat
    }
    return JsonResponse(ret)
