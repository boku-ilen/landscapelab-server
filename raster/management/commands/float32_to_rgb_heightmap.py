import os

import numpy as np
import rasterio
from django.core.management import BaseCommand


class Command(BaseCommand):
    help = """
    This script takes a tif with 1 band of float32 pixels and converts it to an 8bit-channel RGB tif.
    The process is technically lossy, but has enough accuracy for heightmaps to be converted losslessly.
    To reconstruct the height in millimeters from the RGB channels: R * 2^16 + G * 2^8 + B
    
    There are two outputs: The result of the conversion in 'converted.tif', and a human-readable
    (but very lossy!) 'view.tif', in which the encoded values have been converted back - thus it
    can be used to roughly check if the conversion is correct.
    """

    def add_arguments(self, parser):
        parser.add_argument('--imagepath', type=str)

    def handle(self, *args, **options):
        filename = options['imagepath']

        if not filename or not os.path.isfile(filename):
            raise ValueError("Invalid path!")

        with rasterio.open(filename) as src:
            float32input = src.read(1)
            profile = src.profile
            
        # Convert negative pixels to 0, since e.g. nodata may be encoded as -9999
        float32input[float32input < 0] = 0

        # Meters to millimeters
        float_millimeters = float32input * 100

        int_millimeters = float_millimeters.astype(np.uint32)

        # Datatype for array with  4 8bit bands
        # The first band is discarded because heightmaps will never have such big heights (over 167772 meters? nope)
        dt = np.dtype((np.uint32, {'f0': (np.uint8, 0), 'f1': (np.uint8, 1), 'f2': (np.uint8, 2), 'f3': (np.uint8, 3)}))

        # Split the input int_millimeters into an array according to the datatype
        int_split = int_millimeters.view(dtype=dt)

        profile.update(dtype=rasterio.uint8, count=3, compress='lzw', nodata=0)

        with rasterio.open('converted.tif', 'w', **profile) as dst:
            dst.write(int_split['f2'].astype(rasterio.uint8), 1)
            dst.write(int_split['f1'].astype(rasterio.uint8), 2)
            dst.write(int_split['f0'].astype(rasterio.uint8), 3)

        # Also save a reconstructed image to make sure everything is correct
        reconstructed = int_split['f2'].astype(np.uint32) * 2 ** 16 + int_split['f1'].astype(np.uint32) * 2 ** 8 + \
                        int_split['f0'].astype(np.uint32)

        print("Maximum height of reconstructed image in millimeters - compare to gdalinfo -stats to make sure the "
              "data has been encoded correctly:", reconstructed.max())

        reconstructed_scaled = reconstructed * (255.0 / reconstructed.max())

        with rasterio.open('view.tif', 'w', **profile) as dst:
            for i in range(1, 4):
                dst.write(reconstructed_scaled.astype(rasterio.uint8), i)

        print("Done! Produced 'converted.tif' and (lossy, but human-readable) 'view.tif'.")
