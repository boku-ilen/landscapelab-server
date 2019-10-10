import logging

import fiona
from django.contrib.gis.geos import Point
from django.core.exceptions import ObjectDoesNotExist
from django.core.management import BaseCommand

from location.models import Scenario, Location

logger = logging.getLogger(__name__)
NAME_FIELD = "NAME"


# FIXME: this is a hardcoded stub which needs rework and generalization
class Command(BaseCommand):

    help = """
    Takes a .shp file, extracts pois and saves them to the database 
    """

    def add_arguments(self, parser):
        parser.add_argument('--filename', type=str)
        parser.add_argument('--scenario_id', type=int)

    def handle(self, *args, **options):

        # check for necessary parameters
        if 'filename' not in options:
            raise ValueError("no filename given")
        if 'scenario_id' not in options:
            raise ValueError("no scenario_id given")

        filename = options['filename']
        logger.info('starting to import file {}'.format(filename))

        # get scenario and root tile
        try:
            scenario_id = options['scenario_id']
            scenario = Scenario.objects.get(pk=scenario_id)
        except ObjectDoesNotExist:
            logger.error('invalid scenario id: {}'.format(scenario_id))
            raise ValueError('Scenario with id {} does not exist'.format(scenario_id))

        order = 0
        with fiona.open(filename) as shapefile:
            for feature in shapefile:
                coordinates = feature['geometry']['coordinates']
                geometry = Point(coordinates)
                name = feature['properties'][NAME_FIELD]

                location = Location()
                location.scenario = scenario
                location.name = name
                location.direction = 0  # TODO: currently looking north all the time
                location.location = geometry
                location.order = order
                location.save()

                order += 1  # currently there is no order field in the shapefile

        logger.info("finished import to scenario_id {}".format(scenario_id))
