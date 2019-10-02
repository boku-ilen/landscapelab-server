import datetime
import logging
import os
import time

import fiona
from django.contrib.gis.geos import Point, Polygon, LinearRing
from django.core.exceptions import ObjectDoesNotExist
from django.core.management import BaseCommand

from assetpos.models import AssetPositions, Asset, AssetType
from assetpos.models import Tile
from buildings.models import BuildingFootprint
from buildings.views import generate_buildings_with_asset_id
from location.models import Scenario
from raster.tiles import get_root_tile

logger = logging.getLogger(__name__)

MIN_LEVEL_BUILDINGS = 16
HEIGHT_FIELD_NAME = 'HGT_MEAN'
ASSET_TYPE_NAME = 'Building'
PERCENTAGE_LOG_FREQUENCY = 200
FALLBACK_HEIGHT = 3


class Command(BaseCommand):
    help = """
    Takes a .shp file, extracts building footprints, saves them to the database and generates
    the corresponding 3D models.
    Optional parameters can be given to only import or to only generate models.
    """

    def add_arguments(self, parser):
        parser.add_argument('--filename', type=str)
        parser.add_argument('--scenario_id', type=int)
        parser.add_argument('--import_only', action='store_true')
        parser.add_argument('--generate_only', action='store_true')
        parser.add_argument('--regenerate', action='store_true')

    def handle(self, *args, **options):

        # get scenario and root tile
        try:
            scenario_id = options['scenario_id']
            scenario = Scenario.objects.get(pk=scenario_id)
            root_tile = get_root_tile(scenario)
        except ObjectDoesNotExist:
            logger.error('invalid scenario id: {}'.format(scenario_id))
            raise ValueError('Scenario with id {} does not exist'.format(scenario_id))

        # should we only generate the models, not import?
        if options['generate_only']:
            generate_building_models(options['regenerate'], root_tile)
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
                        'building_{}_{}_{}'.format(scenario.name, feat['id'], b_id),
                        root_tile
                    )
                    data[result] += 1

            elif feat['geometry']['type'] is 'Polygon':
                result = save_building_footprint(
                    feat['geometry']['coordinates'][0],
                    feat['properties'][HEIGHT_FIELD_NAME],
                    'building_{}_{}'.format(scenario.name, feat['id']),
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

        if not options['import_only']:
            generate_building_models(options['regenerate'], root_tile)


def generate_building_models(regenerate, tile_id):
    """Gets all buildings from the database and generates their 3D model files"""

    logger.info("Generating building files...")

    gen_buildings = []
    for asset in AssetPositions.objects.filter(asset_type=AssetType.objects.get(name=ASSET_TYPE_NAME),
                                               tile_id=tile_id).all():
        if regenerate or not os.path.exists("buildings/out/{}.glb".format(asset.asset.name)):
            gen_buildings.append(asset.id)

    generate_buildings_with_asset_id(gen_buildings)


def save_building_footprint(absolute_vertices: list, height: float, name: str, root_tile: Tile):
    """Saves one building footprint to the database"""

    if not height:
        logger.warning("Building with name {} does not have a valid height! Setting it to fallback"
                       " of {}m".format(name, FALLBACK_HEIGHT))

    operation = 'new'
    building = None

    # search for existing entry in db
    search_asset = Asset.objects.filter(name=name)
    if search_asset:
        asset_position = AssetPositions.objects.filter(asset=search_asset.first(),
                                                       asset_type=AssetType.objects.get(name=ASSET_TYPE_NAME),
                                                       tile_id=root_tile)
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
        asset_position = AssetPositions(asset=asset, asset_type=AssetType.objects.get(name=ASSET_TYPE_NAME),
                                        tile_id=root_tile)

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
    asset_position.orientation = 0

    asset_position.save()
    building.asset = asset_position
    building.save()

    return operation
