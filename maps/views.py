from django.http import JsonResponse
from .png_to_response import *


# Create your views here.

def index(request):
    return JsonResponse(request_to_png_response(request))
