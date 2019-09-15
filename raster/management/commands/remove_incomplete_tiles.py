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

        if options['check_only']:
            files_to_be_deleted = 0
            files_total = 0

        # Iterate over zoom folder, then x coordinate folder, then y coordinate files within that folder
        for zoom_folder in os.listdir(pyramidpath):
            full_zoom_path = os.path.join(pyramidpath, zoom_folder)

            for x_folder in os.listdir(full_zoom_path):
                full_x_path = os.path.join(full_zoom_path, x_folder)

                for y_file in os.listdir(full_x_path):
                    full_y_file = os.path.join(full_x_path, y_file)

                    if '.png' in full_y_file:
                        if options['check_only']:
                            files_total += 1

                        with rasterio.open(full_y_file) as src:
                            bands = src.read()

                            # Check how many pixels with the value 0 there are per band
                            # TODO: This method is pretty inefficient, but it's done like this because of how
                            #  rasterio structures images... we check every single pixel in every single band
                            #  because we only want to delete tiles which have pixels that are 0 in ALL bands
                            pixels_checked = [0] * len(bands[0][0]) * len(bands[0])

                            for band in bands:
                                pixel_number = 0

                                for row in band:
                                    for pixel in row:
                                        if pixel != 0:
                                            pixels_checked[pixel_number] += 1

                                        pixel_number += 1

                            # If there was a pixel which was 0 in all bands, this image contains empty pixels
                            # -> Print/delete it
                            if 0 in pixels_checked:
                                if options['check_only']:
                                    print("File {} would be removed!".format(full_y_file))
                                    files_to_be_deleted += 1
                                else:
                                    os.remove(full_y_file)
                            elif options['check_only']:
                                print("File {} is fine!".format(full_y_file))

        # Print statistics
        if options['check_only']:
            print("{} tiles of {} - {}% - would be deleted.".format(files_to_be_deleted, files_total,
                                                                    (files_to_be_deleted / files_total) * 100))
