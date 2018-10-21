from django.shortcuts import render
import logging
# Create your views here.
from django.http import JsonResponse

logger = logging.getLogger("MainLogger")


def index(request):
    return JsonResponse({"Error": "not implemented yet"})