import os.path
import logging
import json
from json import JSONDecodeError

from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse
from django.contrib.staticfiles import finders

# Create your views here.
logger = logging.getLogger('MainLogger')


def index(requset):
    if 'filename' not in requset.GET:
        return get_areas()
    filename = requset.GET.get('filename')
    
    return get_area_file(filename)


def get_areas():
    path = finders.find("areas")
    area_files = os.listdir(path)
    area_list = []
    for area in area_files:
        if os.path.splitext(area)[1] == '.json':
            area_list.append(os.path.splitext(area)[0])
    return JsonResponse({"Areas": area_list})


def get_area_file(filename):
    path = finders.find(os.path.join("areas", filename + ".json"))
    logger.info(path)

    if path is None:
        return JsonResponse({"Error": "file does not exist"})

    try:
        with open(path) as f:
            data = json.load(f)
        return JsonResponse(data)
    except JSONDecodeError:
        return JsonResponse({"Error": "invalid JSON data"})
