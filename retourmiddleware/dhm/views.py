from django.http import JsonResponse

from .hdm_to_json import *


# Create your views here.

def index(requset):
    data = getHDM(requset)
    return JsonResponse(data)
