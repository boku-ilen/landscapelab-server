from django.http import JsonResponse

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
