import os

from django.core.management import BaseCommand

# Source of the actual conversion calculation:
# https://alastaira.wordpress.com/2011/07/06/converting-tms-tile-coordinates-to-googlebingosm-tile-coordinates/


class Command(BaseCommand):
    help = 'Converts pyramid tiles from TMS format to OSM by transforming the y coordinate of the tile paths.'

    def add_arguments(self, parser):
        parser.add_argument('--pyramidpath', type=str)

    def handle(self, *args, **options):
        pyramidpath = options['pyramidpath']

        if not pyramidpath or not os.path.isdir(pyramidpath):
            raise ValueError('Invalid path - must be a directory!')

        # Iterate over zoom folder, then x coordinate folder, then y coordinate files within that folder
        for zoom_folder in os.listdir(pyramidpath):
            full_zoom_path = os.path.join(pyramidpath, zoom_folder)
            zoom = int(zoom_folder)

            for x_folder in os.listdir(full_zoom_path):
                full_x_path = os.path.join(full_zoom_path, x_folder)

                for y_file in os.listdir(full_x_path):
                    full_y_file = os.path.join(full_x_path, y_file)

                    if '.png' in full_y_file:
                        # Split the coordinate from the file ending (usually png or png.aux.xml)
                        coordinate_and_ending = y_file.split('.', 1)

                        # Transform the y coordinate to OSM format
                        coordinate = int(coordinate_and_ending[0])
                        new_y_coordinate = (1 << zoom) - coordinate - 1
                        new_y_file = str(new_y_coordinate) + '.' + str(coordinate_and_ending[1])

                        # Build the new filename and rename the file
                        full_new_file = os.path.join(full_x_path, new_y_file)
                        os.rename(full_y_file, full_new_file)
