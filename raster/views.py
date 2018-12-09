from django.http import JsonResponse

from raster.calculate_raster import filename_from_coords
from raster.dhm_to_json import getDHM
from .png_to_response import *


# delivers a static raster file by given filename as json
# TODO: we will use this for textures and precalculated orthos?
def static_raster(request, filename):
    return JsonResponse(request_to_png_response(filename))


# delivers the old dhm format
def get_dhm(request):
    data = getDHM(request)
    return JsonResponse(data)


# returns the pointer to the filename which contains the combined ortho and dhm info
def get_ortho_dhm(request, layer, meter_x, meter_y, zoom):
    filename = filename_from_coords(layer, meter_x, meter_y, zoom)
    return JsonResponse({'filename': filename})
