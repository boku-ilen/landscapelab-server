from django.http import JsonResponse
from django.contrib.staticfiles import finders
from buildings.models import BuildingLayout
from assetpos.models import AssetPositions, Asset, AssetType
from location.models import Scenario
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.gis.geos import Point, Polygon, LinearRing
import os
import fiona
import logging

logger = logging.getLogger('MainLogger')



# scans features of a shp file, saves them to the database and assigns the scenario
def scan_buildings(request, filename : str, scenario_id):
    filename = finders.find(os.path.join('buildings',filename))
    logger.info('starting to import file {}'.format(filename))
    if filename is None:
        logger.info('invalid filename: {}'.format(filename))
        return JsonResponse({'Error': 'unknown filename'})

    try:
        scenario = Scenario.objects.get(pk=scenario_id)
    except ObjectDoesNotExist as error:
        logger.info('invalid scenario id: {}'.format(scenario_id))
        return JsonResponse({'Error': 'scenario with id {} does not exist'.format(scenario_id)})


    if not AssetType.objects.filter(name='building'):
        AssetType(name='building').save()

    data = {'new':0,'updated':0, 'ignored':0, 'error':0}

    file = fiona.open(filename)
    for feat in file:
        if feat['geometry']['type'] is 'MultiPolygon':
            for b_id in range(len(feat['geometry']['coordinates'])):
                result = save_building(feat['geometry']['coordinates'][b_id][0], scenario, '{}_{}'.format(feat['id'], b_id))
                data[result] += 1

        elif feat['geometry']['type'] is 'Polygon':
            result = save_building(feat['geometry']['coordinates'][0], scenario, feat['id'])
            data[result] += 1
            pass

    logger.info('finished importing file {}'.format(filename))
    return JsonResponse({'data': data})


#saves one building to the database
def save_building(vertices : list, scenario : Scenario, name : str):
    name = '{}_{}'.format(scenario.name, name)
    asset = AssetPositions(asset=Asset(name=name), asset_type=AssetType.objects.get(name='building'))
    building = BuildingLayout.objects.filter(asset=asset)
    operation = 'new'
    if building:
        building = building.first() # since name is unique the query set has to have size 1
        operation = 'updated'
    else:
        building = BuildingLayout()

    mean = [0,0]
    for v in vertices:
        mean[0] += v[0]
        mean[1] += v[1]
    mean[0]/=len(vertices)
    mean[1]/=len(vertices)

    vert = []
    for v in vertices:
        vert.append((v[0]-mean[0],v[1]-mean[1]))
    vert = LinearRing(vert)
    vert = Polygon(vert)

    asset.location = Point(mean[0],mean[1])
    building.vertices = vert
    # asset.tile = get_tile(scenario, asset.location) # TODO create get_tile

    asset.save()
    building.asset = asset
    building.save()
    return operation