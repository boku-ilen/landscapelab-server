import webmercator
from django.http import JsonResponse

import calculate_dhm
import process_orthos
from raster.process_orthos import filename_from_coords
from .png_to_response import *


# delivers a static raster file by given filename as json
# TODO: we will use this for textures and precalculated orthos?
def static_raster(request, filename):
    return JsonResponse(request_to_png_response(filename))


# returns the pointer to the filename which contains the combined ortho and dhm info
# TODO: maybe we want to provide the same API with given tile coordinates?
def get_ortho_dhm(request, layer, meter_x, meter_y, zoom):

    # fetch the related filenames
    p = webmercator.Point(meter_x=meter_x, meter_y=meter_y, zoom_level=zoom)
    filename_ortho = process_orthos.get_ortho_from_coords(p.tile_x, p.tile_y, zoom)
    filename_dhmsplat = calculate_dhm.get_dhmsplat_from_coords(p.tile_x, p.tile_y, zoom)

    # answer with a json
    ret = {
        'ortho': filename_ortho,
        'dhmsplat': filename_dhmsplat,
    }
    return JsonResponse(ret)
