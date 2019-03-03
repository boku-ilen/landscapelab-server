from django.http import JsonResponse
from django.contrib.staticfiles import finders
from buildings.models import BuildingLayout
from assetpos.models import AssetPositions, Asset, AssetType
from location.models import Scenario
from assetpos.models import Tile
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.gis.geos import Point, Polygon, LinearRing
import webmercator.point

import os
import fiona
import logging

logger = logging.getLogger('MainLogger')

MIN_LEVEL_BUILDINGS = 16


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
    (leng, fin) = (len(file), 0)
    for feat in file:
        if feat['geometry']['type'] is 'MultiPolygon':
            for b_id in range(len(feat['geometry']['coordinates'])):
                result = save_building(feat['geometry']['coordinates'][b_id][0], scenario, '{}_{}'.format(feat['id'], b_id))
                data[result] += 1

        elif feat['geometry']['type'] is 'Polygon':
            result = save_building(feat['geometry']['coordinates'][0], scenario, feat['id'])
            data[result] += 1
        
        fin += 1
        if fin % 100 == 0:
            logger.debug("done with item {} of {} ({}%)".format(fin, leng, round((fin/leng)*100,1)))

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
        ass = Asset(name=name)
        ass.save()
        asset.asset = ass
        

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
    asset.tile = get_building_tile(scenario, asset.location)
    asset.orientation = 0

    asset.save()
    building.asset = asset
    building.save()
    return operation


def get_building_tile(scenario : Scenario, location : Point):
    tile = get_root_tile(scenario)
    
    while True:
        (x,y) = get_corresponding_tile_coordinates(location, tile.lod+1)
        new_tile = Tile.objects.filter(x=x, y=y, lod=tile.lod+1)
        if not new_tile:
            break
        tile = new_tile.first()
        
       
    # logger.debug("starting at level {} to generate tiles".format(tile.lod))
    
    while tile.lod < MIN_LEVEL_BUILDINGS:
        (x,y) = get_corresponding_tile_coordinates(location, tile.lod+1)
        tile = gen_sub_tile(x,y,tile)
        
    # while True:
    #     children = Tile.objects.filter(parent=tile) # tile.parent_set()
    #     new_tile = tile
    #     for child in children:
    #         if get_bbox(child).contains(location):
    #             new_tile = child
    #             break
    #         logger.debug("child bbox {}, location {}".format(get_bbox_stats(child), location))
    #     if new_tile is tile:
    #         tile = new_tile
    #         break
    #     tile = new_tile
    # 
    # #logger.debug("starting to create new tiles at lod {}".format(tile.lod))
    # while tile.lod < MIN_LEVEL_BUILDINGS:
    #     tile = generate_sub_tile(tile, location)

    return tile


# TODO move to more general context
def gen_sub_tile(x, y, parent : Tile):
    child = Tile(scenario=parent.scenario, parent=parent, x=x, y=y, lod=parent.lod+1)
    child.save()
    
    # TODO move other assets that are in parent and child to child
    
    return child


def get_root_tile(scenario : Scenario):
    # return Tile.objects.get(scenario=scenario, parent='self') # this apparently does not work
    # TODO maybe find a more efficient solution (may be possible with simple statement like in comment above)
    tiles = Tile.objects.filter(scenario=scenario, x=0, y=0, lod=0)
    for tile in tiles:
        if tile.pk == tile.parent.pk:
            return tile

    tile = Tile(scenario=scenario, x=0,y=0, lod=0)
    tile.save()
    tile.parent = tile # maybe tile.parent.save() works (tile.save() does not work because related object 'parent' is unsaved)
    tile.save()
    # generate_dhm_db()
    return tile


def get_corresponding_tile_coordinates(location : Point, lod):
    coord = webmercator.Point(meter_x=location.x, meter_y=location.y, zoom_level=lod)
    return coord.tile_x, coord.tile_y