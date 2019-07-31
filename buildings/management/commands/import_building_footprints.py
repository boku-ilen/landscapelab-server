from django.http import JsonResponse
from django.contrib.staticfiles import finders
from buildings.models import BuildingFootprint
from assetpos.models import AssetPositions, Asset, AssetType
from location.models import Scenario
from assetpos.models import Tile
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.gis.geos import Point, Polygon, LinearRing
from raster.tiles import get_root_tile, get_highest_lod_tile
import webmercator.point
from django.core.management import BaseCommand
import time
import datetime
from buildings.views import generate_buildings_with_asset_id

import os
import fiona
import logging

logger = logging.getLogger(__name__)

MIN_LEVEL_BUILDINGS = 16
HEIGHT_FIELD_NAME = '_mean'
ASSET_TYPE_NAME = 'building'
PERCENTAGE_LOG_FREQUENCY = 200
FALLBACK_HEIGHT = 3


class Command(BaseCommand):
    help = """
    This script takes a .shp file, extracts building footprints and saves them to the database
    """

    def add_arguments(self, parser):
        parser.add_argument('--filename', type=str)
        parser.add_argument('--scenario_id', type=int)
        parser.add_argument('--generate_only', action='store_true')
        parser.add_argument('--regenerate', action='store_true')

    def handle(self, *args, **options):

        # should we only generate the models, not import?
        if options['generate_only']:
            generate_building_models(options['regenerate'])
            return

        # check for necessary parameters
        if 'filename' not in options:
            raise ValueError("no filename given")
        if 'scenario_id' not in options:
            raise ValueError("no scenario_id given")

        filename = options['filename']

        if filename is None:
            logger.error('invalid filename: {}'.format(filename))
            raise ValueError("Invalid filename!")

        logger.info('starting to import file {}'.format(filename))

        # get scenario and root tile
        try:
            scenario_id = options['scenario_id']
            scenario = Scenario.objects.get(pk=scenario_id)
            root_tile = get_root_tile(scenario)
        except ObjectDoesNotExist:
            logger.error('invalid scenario id: {}'.format(scenario_id))
            raise ValueError('Scenario with id {} does not exist'.format(scenario_id))

        data = {'new': 0, 'updated': 0, 'ignored': 0, 'error': 0}

        # parse file
        file = fiona.open(filename)
        max_size, count = (len(file), 0)
        logger.info("Parsing file of size {}".format(max_size))
        time_spent = 0

        for feat in file:
            # Measure how long we take for this one
            starttime = time.time()

            if feat['geometry']['type'] is 'MultiPolygon':
                for b_id in range(len(feat['geometry']['coordinates'])):
                    result = save_building_footprint(
                        feat['geometry']['coordinates'][b_id][0],
                        feat['properties'][HEIGHT_FIELD_NAME],
                        '{}_{}_{}'.format(scenario.name, feat['id'], b_id),
                        root_tile
                    )
                    data[result] += 1

            elif feat['geometry']['type'] is 'Polygon':
                result = save_building_footprint(
                    feat['geometry']['coordinates'][0],
                    feat['properties'][HEIGHT_FIELD_NAME],
                    '{}_{}'.format(scenario.name, feat['id']),
                    root_tile
                )
                data[result] += 1

            count += 1

            delta = time.time() - starttime
            time_spent += delta

            # Update the average duration per entry
            avg_duration = time_spent / count

            # Show percentage every FREQUENCY entries
            if count % PERCENTAGE_LOG_FREQUENCY == PERCENTAGE_LOG_FREQUENCY - 1:
                # Calculate the approx. remaining time by how long we'd take for all remaining entries
                #  with the current average time
                remaining = avg_duration * (max_size - count)

                logger.info("{:7.3f}%, ~{} remaining".format((count / max_size) * 100,
                                                             str(datetime.timedelta(seconds=remaining))))

        logger.info('Finished importing file {}'.format(filename))
        for info, value in data.items():
            logger.info(' - {}: {}'.format(info, value))

        generate_building_models(options['generate_only'])


def generate_building_models(regenerate):
    """Gest all buildings from the database and generates their 3D model files"""

    logger.info("Generating building files...")

    gen_buildings = []
    for asset in AssetPositions.objects.filter(asset_type=AssetType.objects.get(name=ASSET_TYPE_NAME)).all():
        if regenerate or not os.path.exists("buildings/out/{}.glb".format(asset.asset.name)):
            gen_buildings.append(asset.id)

    generate_buildings_with_asset_id(gen_buildings)


# saves one building footprint to the database
def save_building_footprint(absolute_vertices: list, height: float, name: str, root_tile: Tile):
    if not height:
        logger.warning("Building with name {} does not have a valid height! Setting it to fallback"
                       " of {}m".format(name, FALLBACK_HEIGHT))

    operation = 'new'
    building = None

    # search for existing entry in db
    search_asset = Asset.objects.filter(name=name)
    if search_asset:
        asset_position = AssetPositions.objects.filter(asset=search_asset.first(),
                                                       asset_type=AssetType.objects.get(name=ASSET_TYPE_NAME))
        if asset_position:
            asset_position = asset_position.first()
            building = BuildingFootprint.objects.filter(asset=asset_position)

            # check if the corresponding asset already has a building footprint assigned to it
            if building:
                building = building.first()  # since name is unique the query set has to have size 1
                operation = 'updated'

    # create new entry in non could be found
    if not building:
        # create a new building footprint
        building = BuildingFootprint()
        asset = Asset(name=name, asset_type=AssetType.objects.get(name=ASSET_TYPE_NAME))
        asset.save()
        asset_position = AssetPositions(asset=asset, asset_type=AssetType.objects.get(name=ASSET_TYPE_NAME))

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
        relative_vertices.append((v[0] - mean[0], v[1] - mean[1]))
    relative_vertices = LinearRing(relative_vertices)
    relative_vertices = Polygon(relative_vertices)

    # set the values of asset_position and building and save them
    asset_position.location = Point(mean[0], mean[1])
    building.vertices = relative_vertices
    building.height = height
    asset_position.tile = get_highest_lod_tile(asset_position.location, root_tile, MIN_LEVEL_BUILDINGS)
    asset_position.orientation = 0

    asset_position.save()
    building.asset = asset_position
    building.save()

    return operation
