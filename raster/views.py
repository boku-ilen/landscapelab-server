from django.http import JsonResponse

from raster.process_orthos import filename_from_coords
from .png_to_response import *


# delivers a static raster file by given filename as json
# TODO: we will use this for textures and precalculated orthos?
def static_raster(request, filename):
    return JsonResponse(request_to_png_response(filename))


# returns the pointer to the filename which contains the combined ortho and dhm info
def get_ortho_dhm(request, layer, meter_x, meter_y, zoom):
    # TODO: maybe we want to answer more related infos in a complete json?
    # TODO: and also point to the two different tile files (ortho and dhm/splat)?
    filename = filename_from_coords(layer, meter_x, meter_y, zoom)
    return JsonResponse({'f': filename})
