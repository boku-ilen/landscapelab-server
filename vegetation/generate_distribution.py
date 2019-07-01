import os
import random
import logging

from PIL import Image
from django.shortcuts import get_object_or_404
from django.conf import settings

from vegetation.models import Phytocoenosis


DISTRIBUTION_BASE = settings.STATICFILES_DIRS[0] + "/phytocoenosis-distribution/"
DISTRIBUTION_PATHSET = os.path.join(DISTRIBUTION_BASE, "{}")
DISTRIBUTION_PATH = os.path.join(DISTRIBUTION_PATHSET, "{}.png")

IMG_SIZE_IN_METERS = 10
PIXELS_PER_METER = 5

IMG_SIZE = IMG_SIZE_IN_METERS * PIXELS_PER_METER

logger = logging.getLogger(__name__)


def get_random_img_array(number_of_species):
    """Returns an array which can be used to create a distribution image for the given
    number of species. Each species is placed completely randomly - parameters such as
    clumping behavior are not taken into consideration.

    This function will be deprecated as soon as more fine-tuned functions are implemented.
    """

    img_data = []

    # Generate a random value for each pixel
    for x in range(0, IMG_SIZE ** 2):
        img_data.append(random.randint(1, number_of_species))

    return img_data


def get_density_img_array(species):
    """Returns an array with random positions for each species, taking the density into
    account (but not the clumping behavior).

    Plants at each pixel are selected by picking random numbers for each species, multiplied
    by the density. The species with the highest number gets inserted.
    """

    # TODO: The distribution_density is in occurances/m². We'll need to extent this algorithm
    #  to realistically use that value.

    ids = [sp.id for sp in species]

    img_data = []

    # Generate a random value for each pixel
    for x in range(0, IMG_SIZE ** 2):
        new_id = 0
        highest_roll = 0

        for s in species:
            dice = random.random() * s.distribution_density
            if dice >= highest_roll:
                highest_roll = dice
                new_id = s.id

        # In the distribution, the index of this ID is used. This is because the shader which uses
        #  these images doesn't care about the actual species IDs anymore, it just enumerates them
        #  starting at 1. (0 means that nothing should be drawn there.)
        img_data.append(ids.index(new_id) + 1 if new_id > 0 else 0)

    return img_data


def generate_distribution_for_phytocoenosis_and_layer(phyto_c_id, layer):
    """Generates and saves a distribution image for a phytocoenosis at the given layer.

    The pixel's red values correspond to the speciesRepresentations, starting at 1. A value
    of 0 means that no plant should be placed at that location.

    Example: With phyto_c_id=2 and layer=5, the image is saved to
    /phytocoenosis-distribution/2/5.png
    """

    # Create all required directories if they don't yet exist
    pathset = DISTRIBUTION_PATHSET.format(phyto_c_id)

    if not (os.path.exists(DISTRIBUTION_BASE)):
        os.mkdir(DISTRIBUTION_BASE)

    if not (os.path.exists(pathset)):
        os.mkdir(pathset)

    # Get the speciesRepresentations in the phytocoenosis
    species = get_object_or_404(Phytocoenosis, id=phyto_c_id) \
        .speciesRepresentations.filter(vegetation_layer=layer).all()

    # Create an image with randomly spread values for the species IDs
    img = Image.new("L", size=(IMG_SIZE, IMG_SIZE))
    img.putdata(get_density_img_array(species))

    filename = DISTRIBUTION_PATH.format(phyto_c_id, layer)
    img.save(filename)


def get_distribution_for_id_and_layer(phyto_c_id, layer):
    """Returns the path to the spritesheet containing all plant images for a given
    phytocoenosis ID and layer. If the file does not exist yet, it is generated.
    """

    filename = DISTRIBUTION_PATH.format(phyto_c_id, layer)

    if not os.path.isfile(filename):
        logger.info("Generating distribution for {}...".format(filename))
        generate_distribution_for_phytocoenosis_and_layer(phyto_c_id, layer)

    # If the file now exists, return it
    if os.path.isfile(filename):
        return filename
