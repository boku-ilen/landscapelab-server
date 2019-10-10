
from django.http import JsonResponse
from django.core.files.storage import default_storage
from buildings.models import BuildingFootprint
from assetpos.models import AssetPositions, AssetType
from django.contrib.gis.geos import Polygon
import os
import logging
import subprocess


logger = logging.getLogger(__name__)

BUILDING_PATH = 'buildings'
BUILDING_IDENTIFIER = 'building'  # this is asset_type id 1

MAX_BUILDINGS_AT_ONCE = 100  # Blender is invoked separately in blocks of this many buildings


# FIXME: just for test purposes
def get_from_bbox(request, x_min, y_min, x_max, y_max):
    # useful test parameters: 4583980.1/2739338.7/4583860.7/2739418.7
    bbox = Polygon.from_bbox((x_min, y_min, x_max, y_max))
    return get_buildings_in_bbox(bbox)


# FIXME: just for test purposes
def get_buildings_in_bbox(bbox: Polygon):
    assets = AssetPositions.objects.filter(location__contained=bbox,
                                           asset_type=AssetType.objects.get(BUILDING_IDENTIFIER))
    data = []
    to_create = []

    for building in assets:
        p = []
        p.extend(building.location)
        data.append({'name': building.asset.name, 'position': p})
        if not default_storage.exists(os.path.join(BUILDING_PATH, '{}.dae'.format(building.asset.name))):
            to_create.append(BuildingFootprint.objects.get(asset=building).pk)

    if to_create:
        logger.debug('creating {} new buildings'.format(len(to_create)))

        params = ['blender', '--background', '--python', '{}/create_buildings.py'.format('buildings'), '--']
        for b in to_create:
            params.append(str(b))
        subprocess.run(params)

        logger.debug('finished creating buildings')

    return JsonResponse({'data': data})


# generates and exports all buildings linked to specified asset IDs
def generate_buildings_with_asset_id(asset_ids):

    assets = AssetPositions.objects.filter(pk__in=asset_ids)
    building_ids = []

    # get the corresponding building IDs to the asset IDs (also filters out any non building assets)
    for asset in assets:
        building_ids.append(BuildingFootprint.objects.get(asset=asset).pk)

    if building_ids:
        # Iterate over building_ids in chunks
        for i in range(0, len(building_ids), MAX_BUILDINGS_AT_ONCE):
            building_ids_chunk = building_ids[i:i + MAX_BUILDINGS_AT_ONCE]

            logger.info('creating {} new buildings'.format(len(building_ids_chunk)))

            # start blender in background as a subprocess and add building IDs as parameters
            params = ['blender', '--background', '--python', 'buildings/create_buildings.py', '--']
            for b in building_ids_chunk:
                params.append(str(b))

            process = subprocess.run(params)
            return_code = process.returncode

            if return_code != 0:
                print("There was an error! Return code: {}".format(return_code))

        logger.info('finished creating buildings')


# def find_buildings(x_min, y_min, x_max, y_max):
#     bbox = Polygon.from_bbox ((x_min, y_min, x_max, y_max))
#     return BuildingLayout.objects.filter(position__contained=bbox)
