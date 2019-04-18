from django.http import JsonResponse
from django.contrib.staticfiles import finders
from buildings.models import BuildingFootprint
from assetpos.models import AssetPositions, Asset, AssetType
from location.models import Scenario
from assetpos.models import Tile
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.gis.geos import Point, Polygon, LinearRing
import webmercator.point

import os
import fiona
import logging


logger = logging.getLogger(__name__)

MIN_LEVEL_BUILDINGS = 16


# scans features of a shp file, saves them to the database and assigns the scenario
def scan_buildings(request, filename: str, scenario_id):

    # find file
    filename = finders.find(os.path.join('buildings', filename))
    logger.info('starting to import file {}'.format(filename))
    if filename is None:
        logger.warning('invalid filename: {}'.format(filename))
        return JsonResponse({'Error': 'unknown filename'})

    # get scenario and root tile
    try:
        scenario = Scenario.objects.get(pk=scenario_id)
        root_tile = get_root_tile(scenario)
    except ObjectDoesNotExist:
        logger.warning('invalid scenario id: {}'.format(scenario_id))
        return JsonResponse({'Error': 'scenario with id {} does not exist'.format(scenario_id)})

    # create AssetType building if it does not exist
    if not AssetType.objects.filter(name='building'):
        AssetType(name='building').save()

    data = {'new': 0, 'updated': 0, 'ignored': 0, 'error': 0}

    # parse file
    file = fiona.open(filename)
    max_size, count = (len(file), 0)
    for feat in file:
        if feat['geometry']['type'] is 'MultiPolygon':
            for b_id in range(len(feat['geometry']['coordinates'])):
                result = save_building_footprint(
                    feat['geometry']['coordinates'][b_id][0],
                    '{}_{}_{}'.format(scenario.name, feat['id'], b_id),
                    root_tile
                )
                data[result] += 1

        elif feat['geometry']['type'] is 'Polygon':
            result = save_building_footprint(
                feat['geometry']['coordinates'][0],
                '{}_{}'.format(scenario.name, feat['id']),
                root_tile
            )
            data[result] += 1

        count += 1
        # log status update every 100 entries
        if count % 100 == 0:
            logger.debug("done with item {} of {} ({}%)".format(count, max_size,
                                                                round((count/max_size)*100, 1)))

    logger.info('finished importing file {}'.format(filename))
    return JsonResponse({'data': data})


# saves one building footprint to the database
def save_building_footprint(absolute_vertices: list, name: str, root_tile: Tile):

    asset_position = AssetPositions(asset=Asset(name=name), asset_type=AssetType.objects.get(name='building'))
    building = BuildingFootprint.objects.filter(asset=asset_position)
    operation = 'new'

    # check if the corresponding asset already has a building footprint assigned to it
    if building:
        building = building.first()  # since name is unique the query set has to have size 1
        operation = 'updated'

    else:
        # create a new building footprint
        building = BuildingFootprint()
        asset = Asset(name=name, asset_type=AssetType.objects.get(name='building'))
        asset.save()
        asset_position.asset = asset

    # calculate the mean point
    # of the polygons vertices
    mean = [0, 0]
    for v in absolute_vertices:
        mean[0] += v[0]
        mean[1] += v[1]
    mean[0] /= len(absolute_vertices)
    mean[1] /= len(absolute_vertices)

    # calculate the relative positions of all vertices
    # towards the mean point and store them as Polygon
    relative_vertices = []
    for v in absolute_vertices:
        relative_vertices.append((v[0]-mean[0], v[1]-mean[1]))
    relative_vertices = LinearRing(relative_vertices)
    relative_vertices = Polygon(relative_vertices)

    # set the values of asset_position and building and save them
    asset_position.location = Point(mean[0], mean[1])
    building.vertices = relative_vertices
    asset_position.tile = get_highest_lod_tile(asset_position.location, root_tile, MIN_LEVEL_BUILDINGS)
    asset_position.orientation = 0

    asset_position.save()
    building.asset = asset_position
    building.save()

    return operation


# returns the highest LOD (or LOD = max_lod) tile that contains the specified location
# if the LOD is not high enough new tiles will be generated
# TODO binary search for the highest currently existing tile could significantly increase performance
def get_highest_lod_tile(location: Point, parent_tile: Tile, min_lod: int, max_lod: int = 28):

    # break recursion if LOD has reached
    # the specified max value
    if parent_tile.lod >= max_lod:
        return parent_tile

    # get x and y coordinate for the next lod and look for a matching tile
    x, y = get_corresponding_tile_coordinates(location, parent_tile.lod + 1)
    child_tile = Tile.objects.filter(x=x, y=y, lod=parent_tile.lod + 1)

    # if no matching tile could be found
    # check if the LOD is high enough
    if not child_tile:
        if parent_tile.lod >= min_lod:
            # return if LOD is high enough
            return parent_tile

        else:
            # create missing LODs if it is not high enough
            return generate_sub_tiles(parent_tile, location, min_lod)

    # continue recursion until the highest LOD tile is found
    return get_highest_lod_tile(location, child_tile.first())


# recursively generates sub-tiles, from one specific tile with low LOD until
# the LOD hits the specified target_lod
# the last generated Tile will be returned
def generate_sub_tiles(parent_tile: Tile, location: Point, target_lod: int):

    # break recursion and return highest LOD tile if LOD is high enough
    if parent_tile.lod >= target_lod:
        return parent_tile

    # generate tile with higher LOD
    x, y = get_corresponding_tile_coordinates(location, parent_tile.lod + 1)
    child_tile = gen_sub_tile(x, y, parent_tile)

    # continue recursion until LOD is high enough
    return generate_sub_tiles(child_tile, location, target_lod)


# TODO move to more general context
# generates a child-tile of specified parent-tile
def gen_sub_tile(x, y, parent: Tile):
    child = Tile(scenario=parent.scenario, parent=parent, x=x, y=y, lod=parent.lod + 1)
    child.save()
    
    # TODO move other assets that are in parent and child to child
    
    return child


# returns the root tile of specified scenario
def get_root_tile(scenario: Scenario):

    # return Tile.objects.get(scenario=scenario, parent='self') # this apparently does not work
    # TODO maybe find a more efficient solution (may be possible with simple statement like in comment above)

    # find tile with
    tiles = Tile.objects.filter(scenario=scenario, x=0, y=0, lod=0)
    for tile in tiles:
        if tile.pk == tile.parent.pk:
            return tile

    # create a new root tile if none could be found
    tile = Tile(scenario=scenario, x=0, y=0, lod=0)
    tile.save()
    tile.parent = tile  # maybe tile.parent.save() works (tile.save() does not work because related object 'parent' is unsaved)
    tile.save()
    # generate_dhm_db()

    return tile


# returns the x and y coordinates of the tile that
# contains the specified location and has the specified LOD
def get_corresponding_tile_coordinates(location: Point, lod):

    coord = webmercator.Point(meter_x=location.x, meter_y=location.y, zoom_level=lod)
    return coord.tile_x, coord.tile_y
