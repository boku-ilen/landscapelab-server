from django.core.management import BaseCommand
import fiona

class Command(BaseCommand):
    help = 'calculate the maximum extent of the view of field based on an polygon and the DHM'

    def add_arguments(self, parser):
        parser.add_argument('--points-shapefile', type=str, nargs="1")
        parser.add_argument('--dhm-raster', type=str, nargs="1")

    def handle(self, *args, **options):
        dhm_raster = options['dhm-raster']
        with fiona.open(options['points-shapefile']) as points:
            for point in points:
                pass
