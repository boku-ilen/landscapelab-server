import logging
import json
from fiona import collection
import fiona.crs
import shapely.wkt
from django.core.management import BaseCommand
from shapely.geometry import mapping

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """
    Takes a .json file and extracts the positioned assets and write them into a shapefile
    """

    def add_arguments(self, parser):
        parser.add_argument('--filename', type=str)

    def handle(self, *args, **options):

        # check for necessary parameters
        if 'filename' not in options:
            raise ValueError("no filename given")

        filename = options['filename']

        if filename is None:
            logger.error('invalid filename: {}'.format(filename))
            raise ValueError("Invalid filename!")

        logger.info('starting to import file {}'.format(filename))

        schema = {
            'geometry': 'Point',
            'properties': {
                'asset_type': 'int',
                'asset': 'int',
                'create_stamp': 'str'
            }
        }

        with collection(filename + ".shp", 'w', crs=fiona.crs.from_epsg(3857),
                        schema=schema, driver='ESRI Shapefile') as sink:

            with open(filename, 'r') as source:
                assetpositions = json.load(source)

                for assetpos in assetpositions:
                    data = dict()
                    data['geometry'] = mapping(shapely.wkt.loads(assetpos["fields"]["location"][10:]))
                    data['properties'] = dict()
                    data['properties']['asset_type'] = assetpos["fields"]["asset_type"]
                    data['properties']['asset'] = assetpos["fields"]["asset"]
                    data['properties']['create_stamp'] = assetpos["fields"]["create_stamp"]
                    sink.write(data)
