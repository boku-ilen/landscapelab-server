from django.http import JsonResponse

from .dhm_to_json import *


# Create your views here.

def index(requset):
    data = getDHM(requset)
    return JsonResponse(data)