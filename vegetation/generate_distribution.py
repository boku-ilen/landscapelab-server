import os
import random

from PIL import Image
from django.shortcuts import get_object_or_404

from vegetation.models import Phytocoenosis
from vegetation.vegetation_distribution import DISTRIBUTION_PATH, DISTRIBUTION_PATHSET, DISTRIBUTION_BASE

IMG_SIZE_IN_METERS = 10
PIXELS_PER_METER = 5

IMG_SIZE = IMG_SIZE_IN_METERS * PIXELS_PER_METER


def get_random_img_array(number_of_species):
    """Returns an array which can be used to create a distribution image for the given number of species.
    Each species is placed completely randomly - parameters such as clumping behavior are not taken into consideration.

    This function will be deprecated as soon as more fine-tuned functions are implemented.
    """

    img_data = []

    # Generate a random value for each pixel
    for x in range(0, IMG_SIZE ** 2):
        img_data.append(random.randint(1, number_of_species))

    return img_data


def get_density_img_array(species):
    """Returns an array with random positions for each species, taking the density into account (but not the clumping
    behavior).

    Plants are selected like this:
    If there is only one SpeciesRepresentation with full density (1), the chance for it to spawn is 50:50.
    If there are two SpeciesRepresentations with full density, the chance for one of them is 1/3.
    If there are two SpeciesRepresentations, one with full density, another with a density of 1/2, the chance for the
    one with full density is 1/3, and the chance for the one with half density is 1/6.
    etc.
    """

    number_of_species = len(species)

    img_data = []

    # Generate a random value for each pixel
    for x in range(0, IMG_SIZE ** 2):
        new_id = 0

        for s in species:
            dice = random.randint(0, int(1 / (s.distribution_density / number_of_species)))
            if dice == 1:
                new_id = s.id
                break

        img_data.append(new_id)

    return img_data


def generate_distribution_for_phytocoenosis(pid):
    """Generates and saves a distribution image for a whole phytocoenosis.

    The pixel's red values correspond to the speciesRepresentations, starting at 1. A value of 0 means that no plant
    should be placed at that location.

    Example: With pid=2, the image is saved to /phytocoenosis-distribution/2/complete.png
    """

    # Create all required directories if they don't yet exist
    pathset = DISTRIBUTION_PATHSET.format(pid)

    if not (os.path.exists(DISTRIBUTION_BASE)):
        os.mkdir(DISTRIBUTION_BASE)

    if not (os.path.exists(pathset)):
        os.mkdir(pathset)

    # Get the speciesRepresentations in the phytocoenosis
    species = get_object_or_404(Phytocoenosis, id=pid).speciesRepresentations.all()

    # Create an image with randomly spread values for the species IDs
    img = Image.new("L", size=(IMG_SIZE, IMG_SIZE))
    img.putdata(get_density_img_array(species))

    filename = DISTRIBUTION_PATH.format(pid, "complete")
    img.save(filename)


def generate_distribution_for_phytocoenosis_and_layer(pid, layer):
    """Generates and saves a distribution image for a phytocoenosis at a specific layer.
    If there is no complete distribution image yet, it is generated first.
    """

    # Create all required directories if they don't yet exist
    pathset = DISTRIBUTION_PATHSET.format(pid)

    if not (os.path.exists(DISTRIBUTION_BASE)):
        os.mkdir(DISTRIBUTION_BASE)

    if not (os.path.exists(pathset)):
        os.mkdir(pathset)

    # Fetch the complete generation, generate it first if necessary
    complete_filename = DISTRIBUTION_PATH.format(pid, "complete")

    if not os.path.isfile(complete_filename):
        generate_distribution_for_phytocoenosis(pid)

    complete_image = Image.open(complete_filename)

    # Get the IDs in this layer
    representations = get_object_or_404(Phytocoenosis, id=pid)\
        .speciesRepresentations.filter(vegetation_layer=layer).all()
    ids = [rep.id for rep in representations]

    # Create a new image and paste the complete one
    layer_filename = DISTRIBUTION_PATH.format(pid, layer)
    layer_image = Image.new("L", size=(IMG_SIZE, IMG_SIZE))
    layer_image.paste(complete_image)

    pixels = layer_image.load()

    # Replace pixels so that, instead of the phytocoenosis ID, they become the layer ID
    for x in range(IMG_SIZE):
        for y in range(IMG_SIZE):
            if pixels[x, y] in ids:
                # Replace
                new = 1 + ids.index(pixels[x, y])
                pixels[x, y] = new
            else:
                # Nothing here
                pixels[x, y] = 0

    # Save the image
    layer_image.save(layer_filename)
