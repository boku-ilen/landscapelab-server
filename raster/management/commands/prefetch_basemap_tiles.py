from django.core.management import BaseCommand
from location.models import Scenario
import django.contrib.gis.geos as geos

from raster.calculate_raster import fetch_wmts_tiles


class Command(BaseCommand):
    help = 'prefetches the raster ortho tiles from the austrian basemap in given area'

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group()
        group.add_argument('extent', type=str, nargs='?')
        parser.add_argument('srid', type=int, nargs='?')
        group.add_argument('scenario', type=int, nargs='?')
        parser.add_argument('url', type=str, nargs='?')

    def handle(self, *args, **options):

        # get the bounding box we will work with
        bounding_box = None  # defaults to None
        if options['scenario']:
            scenario = Scenario.objects.get(pk=options['scenario'])
            bounding_box = scenario.bounding_polygon.envelope
        if options['extent']:
            if options['srid']:
                srid = options['srid']
            else:
                srid = 3857  # web mercator auxiliary sphere
            bounding_box = geos.fromstr(options['extent'], srid)

        # now we hand off to the internal implementation
        if options['url']:
            fetch_wmts_tiles(bounding_box, url=options['url'])
        else:
            fetch_wmts_tiles(bounding_box)
