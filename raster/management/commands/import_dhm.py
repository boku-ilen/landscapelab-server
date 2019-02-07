from django.core.management import BaseCommand

from raster.calculate_dhm import import_dhm
from location.models import Scenario
import django.contrib.gis.geos as geos


class Command(BaseCommand):
    help = 'applies the height information to a given project or extent'

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group()
        group.add_argument('--bounding_polygon', type=str, nargs='?')
        parser.add_argument('--srid', type=int, nargs='?')
        group.add_argument('--scenario', type=int, nargs='?')
        parser.add_argument('--filename', type=str)

    def handle(self, *args, **options):

        # get the bounding box we will work with
        bounding_box = None  # defaults to None
        if options['srid']:
            srid = options['srid']
        else:
            srid = 3857  # web mercator auxiliary sphere
        if options['scenario']:
            scenario = Scenario.objects.get(pk=options['scenario'])
            bounding_box = scenario.bounding_polygon
        if options['bounding_polygon']:
            bounding_box = geos.fromstr(options['bounding_polygon'], srid=srid)

        # now we hand off to the internal implementation
        import_dhm(options['filename'], bounding_box, srid=srid)
