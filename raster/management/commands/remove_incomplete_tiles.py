import os

import rasterio
from django.core.management import BaseCommand


class Command(BaseCommand):
    help = 'Removes tiles in a tile pyramid which are incomplete (contain transparency).' \
           'E.g. necessary when combining tilesets to prevent cliffs from forming when a file is replaced with an' \
           'incomplete one.' \
           'When the check_only flag is set, the command only prints out files which would be deleted, but doesnt' \
           'actually delete them.'

    def add_arguments(self, parser):
        parser.add_argument('--pyramidpath', type=str)
        parser.add_argument('--check_only', action='store_true')

    def handle(self, *args, **options):
        pyramidpath = options['pyramidpath']

        if not pyramidpath or not os.path.isdir(pyramidpath):
            raise ValueError('Invalid path - must be a directory!')

        # Iterate over zoom folder, then x coordinate folder, then y coordinate files within that folder
        for zoom_folder in os.listdir(pyramidpath):
            full_zoom_path = os.path.join(pyramidpath, zoom_folder)

            for x_folder in os.listdir(full_zoom_path):
                full_x_path = os.path.join(full_zoom_path, x_folder)

                for y_file in os.listdir(full_x_path):
                    full_y_file = os.path.join(full_x_path, y_file)

                    if '.png' in full_y_file:
                        with rasterio.open(full_y_file) as src:
                            bands = src.read()

                            # Check whether the last band (which is the ALPHA channel) contains 0 values
                            got_nulls = 0 in bands[-1]

                            # If there were pixels with 0 alpha, print/delete it
                            if got_nulls:
                                if options['check_only']:
                                    print("File {} contains transparency and would be removed!".format(full_y_file))
                                else:
                                    os.remove(full_y_file)
