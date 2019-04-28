from django.core.management import BaseCommand

from raster.process_maps import fetch_tiles


class Command(BaseCommand):
    help = 'prefetches the opentopomap by default'

    def add_arguments(self, parser):
        parser.add_argument('scenario', type=int)
        parser.add_argument('--url', type=str, nargs=1)
        parser.add_argument('--layer', type=str, nargs=1)
        parser.add_argument('--zoom-from', type=int, nargs='?')
        parser.add_argument('--zoom-to', type=int, nargs='?')

    def handle(self, *args, **options):

        # now we hand off to the internal implementation
        kwargs = dict()
        scenario_id = options['scenario']
        if 'url' in options:
            if options['url']:
                kwargs['tile-url'] = options['url']
        if 'layer' in options:
            if options['layer']:
                kwargs['layer'] = options['layer'][0]  # FIXME: why I have to do this?
        if 'zoom-from' in options:
            if options['zoom-from']:
                kwargs['zoom_from'] = options['zoom-from']
        if 'zoom-to' in options:
            if options['zoom-to']:
                kwargs['zoom_to'] = options['zoom-to']

        fetch_tiles(scenario_id, **kwargs)
