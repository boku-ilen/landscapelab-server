from django.http import JsonResponse
from .png_to_response import *


# delivers a static raster file by given filename as json
def static_raster(request, filename):
    return JsonResponse(request_to_png_response(filename))
