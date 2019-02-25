#TODO THIS FILE IS DEPRECATED AND IT'S CODE SHOULD NO LONGER BE USED; REMOVE IF THE CLIENT NO LONGER RELIES ON IT
from django.http import JsonResponse
from django.core.files.storage import default_storage
from buildings.apps import BuildingsConfig
from buildings.models import BuildingLayout
from assetpos.models import AssetPositions, AssetType
from django.contrib.gis.geos import Polygon
import os
import logging
import subprocess

logger = logging.getLogger('MainLogger')



# def get_buildings(request, zoom, tile_x, tile_y, assettype_id):
#     return JsonResponse({'data':['asdf']})

# just for test purposes
def get_from_bbox(request, x_min, y_min, x_max, y_max):
    # useful test parameters: 4583980.1/2739338.7/4583860.7/2739418.7
    bbox = Polygon.from_bbox ((x_min, y_min, x_max, y_max))
    return get_buildings_in_bbox(bbox)

# just for test purposes
def get_buildings_in_bbox(bbox : Polygon):
    assets = AssetPositions.objects.filter(location__contained=bbox, asset_type=AssetType.objects.get('building'))
    data = []
    to_create = []
    for building in assets:
        p = []
        p.extend(building.location)
        data.append({'name': building.asset.name,'position' : p})
        if not default_storage.exists(os.path.join(BuildingsConfig.name, '{}.dae'.format(building.asset.name))):
            to_create.append(BuildingLayout.objects.get(asset=building).pk)


    if to_create:
        logger.info('creating {} new buildings'.format(len(to_create)))

        params = ['blender', '--background', '--python', '{}/create_buildings.py'.format(BuildingsConfig.name), '--']
        for b in to_create:
            params.append(str(b))
        subprocess.run(params)

        logger.info('finished creating buildings')

    return JsonResponse({'data': data})


# def find_buildings(x_min, y_min, x_max, y_max):
#     bbox = Polygon.from_bbox ((x_min, y_min, x_max, y_max))
#     return BuildingLayout.objects.filter(position__contained=bbox)

# TODO write function for when asset pos asks for buildings (necessary because the exported buildings might not even exist yet)








#TODO DEPRECATED CODE; REMOVE
# OLD DEPRECATED CODE OLD DEPRECATED CODE OLD DEPRECATED CODE OLD DEPRECATED CODE OLD DEPRECATED CODE OLD DEPRECATED CODE OLD DEPRECATED CODE
from buildings.building_to_json import get_buildings
from django.http import JsonResponse
import os.path
from django.contrib.staticfiles import finders

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
