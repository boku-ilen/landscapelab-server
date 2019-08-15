import os

from django.core.management import BaseCommand

# Source of the actual conversion calculation:
# https://alastaira.wordpress.com/2011/07/06/converting-tms-tile-coordinates-to-googlebingosm-tile-coordinates/


class Command(BaseCommand):
    help = 'Converts pyramid tiles from TMS format to OSM by transforming the y coordinate of the tile paths. ' \
           'If the do_austria_check flag is set, only tiles which seem to have the incorrect format for Austrian' \
           ' tiles are renamed.'

    def add_arguments(self, parser):
        parser.add_argument('--pyramidpath', type=str)
        parser.add_argument('--do_austria_check', action='store_true')

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

                x_coordinate = int(x_folder)

                for y_file in os.listdir(full_x_path):
                    full_y_file = os.path.join(full_x_path, y_file)

                    if '.png' in full_y_file:
                        # Split the coordinate from the file ending (usually png or png.aux.xml)
                        coordinate_and_ending = y_file.split('.', 1)

                        # Transform the y coordinate to OSM format
                        y_coordinate = int(coordinate_and_ending[0])

                        if options['do_austria_check']:
                            # In Austria, the y coordinate of correctly named tiles is always smaller than the x
                            # coordinate. If that's the case, don't do anything
                            if x_coordinate > y_coordinate:
                                continue

                        new_y_coordinate = (1 << zoom) - y_coordinate - 1
                        new_y_file = str(new_y_coordinate) + '.' + str(coordinate_and_ending[1])

                        # Build the new filename and rename the file
                        full_new_file = os.path.join(full_x_path, new_y_file)
                        os.rename(full_y_file, full_new_file)

                        print("Renamed {} to {}".format(full_y_file, full_new_file))
