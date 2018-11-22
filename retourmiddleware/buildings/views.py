from django.shortcuts import render
import logging
from .building_to_json import get_buildings
from django.http import JsonResponse
import os.path
from django.contrib.staticfiles import finders


logger = logging.getLogger("MainLogger")
BASE = 'buildings'


def index(request):
    if 'filename' not in request.GET:
        return JsonResponse({"Error": "no filename specified"})
    # get parameters
    filename = request.GET.get('filename')

    # set modifiers
    try:
        modifiers = get_modifiers(request)
    except ValueError:
        return JsonResponse({"Error": "invalid modifier arguments"})

    # add filename to modifiers
    modifiers['filename'] = finders.find(os.path.join(BASE, filename + ".shp"))
    if modifiers['filename'] is None:
        return JsonResponse({"Error": "file %s.shp does not exist" % filename})

    logger.debug(modifiers)
    return JsonResponse(get_buildings(modifiers))


def get_modifiers(request):
    modifiers = dict(
        splits=int(request.GET.get('splits') if 'splits' in request.GET else 1),
        part=int(request.GET.get('part') if 'part' in request.GET else 0)
    )
    return modifiers
