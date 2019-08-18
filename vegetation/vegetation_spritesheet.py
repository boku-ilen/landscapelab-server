import logging
import math
import os

from PIL import Image
from django.shortcuts import get_object_or_404

from landscapelab import utils
from vegetation.models import Phytocoenosis
from vegetation.models import LAYER_MAXHEIGHTS

SPRITE_BASEPATH = "phytocoenosis-spritesheet"
REPRESENTATION_BASEPATH = "plants"
REPRESENTATION_PATHSET = os.path.join(REPRESENTATION_BASEPATH, "{}")
SPRITE_PATHSET = os.path.join(SPRITE_BASEPATH, "{}")
SPRITE_FILE = os.path.join(SPRITE_PATHSET, "{}.png")
SPRITE_COUNT_FILE = os.path.join(SPRITE_PATHSET, "{}.count")

MAX_SPRITE_SIZE = 1024
MAX_SPRITE_ROW = 16

logger = logging.getLogger(__name__)


def generate_spritesheet(phyto_c_id, layer):
    """Generates the spritesheet containing all plant images for a given
    phytocoenosis ID and layer. Also saves the number of sprites in this
    sheet in a separate file.

    If the phytocoenosis does not exist, Error 404 is raised. If there are
    no applicable sprites, the spritesheet is not created, but the count
    of 0 is saved.

    Example: With phyto_c_id=2 and layer=1, the resulting path would be
    /phytocoenosis-spritesheet/2/1.png, with the number of sprites being
    stored in /phytocoenosis-spritesheet/2/1.count
    """

    # Create all required directories if they don't yet exist
    pathset = utils.get_full_texture_path(SPRITE_PATHSET.format(phyto_c_id))
    if not (os.path.exists(pathset)):
        os.makedirs(pathset)

    # Get the required objects from the database
    representations = get_object_or_404(Phytocoenosis, id=phyto_c_id) \
        .speciesRepresentations.filter(vegetation_layer=layer).all()
    sprite_paths = [utils.get_full_texture_path(rep.billboard) for rep in representations]
    number_of_sprites = len(sprite_paths)

    # Write the number of sprites in this sheet to a file
    count_filename = utils.get_full_texture_path(SPRITE_COUNT_FILE.format(phyto_c_id, layer))

    with open(count_filename, "w+") as count_file:
        count_file.write("{}\n".format(number_of_sprites))

    # If there are no sprites for this phytocoenosis, we don't have to do anything.
    # This is a valid use case for something like asphalt or ice.
    if number_of_sprites == 0:
        logger.info("No sprites in phytocoenosis {} at layer {} - could not create spritesheet!".format(phyto_c_id,
                                                                                                        layer))
        return

    # Open all sprites at the sprite_paths using Pillow
    sprites = list(map(Image.open, sprite_paths))

    for index, sprite in enumerate(sprites):
        # Scale the sprite to a maximum of MAX_SPRITE_SIZE and scale it down to match its
        # size relative to its layer's max size
        scale_factor = representations[index].avg_height * MAX_SPRITE_SIZE / LAYER_MAXHEIGHTS[int(layer) - 1][1]

        sprite.thumbnail((scale_factor, scale_factor))

    # Calculate the rows and columns we need
    cols = min(number_of_sprites, MAX_SPRITE_ROW)
    rows = math.ceil(number_of_sprites / MAX_SPRITE_ROW)

    spritesheet = Image.new('RGBA', (MAX_SPRITE_SIZE * cols, MAX_SPRITE_SIZE * rows))

    # Iterate over all sprites and paste them in the spritesheet, at the correct height
    # to have every sprite reach the bottom of the image
    col, row = 0, 0
    for sprite in sprites:
        width, height = sprite.size

        x_offset = col * MAX_SPRITE_SIZE
        y_offset = row * MAX_SPRITE_SIZE

        # Paste the scaled sprite into the spritesheet at the current offset, and also
        # center (x) + floor (y) the object
        spritesheet.paste(sprite, (x_offset + int((MAX_SPRITE_SIZE - width) / 2),
                                   y_offset + MAX_SPRITE_SIZE - height))
        col += 1

        # Jump to the next row if necessary
        if col >= MAX_SPRITE_ROW:
            col = 0
            row += 1

    # Save the spritesheet
    filename = utils.get_full_texture_path(SPRITE_FILE.format(phyto_c_id, layer))
    spritesheet.save(filename)

    logging.info("Sprite saved into {}".format(filename))


def get_count(phyto_c_id, layer):
    """Accesses the .count file for a spritesheet and returns the value within,
    cast to an integer. The file must exist, otherwise an IOError is raised. If the
    file is empty or invalid, the value 0 is returned, and the error is logged.

    As the handling for spritesheet generation is done there, this function is
    supposed to only be called in get_spritesheet_and_count_for_id_and_layer.
    """

    count_filename = utils.get_full_texture_path(SPRITE_COUNT_FILE.format(phyto_c_id, layer))

    if not os.path.isfile(count_filename):
        raise IOError("The requested count file {} does not exist - the function get_count should only be called in "
                      "get_spritesheet_and_count_for_id_and_layer!".format(count_filename))

    with open(count_filename, "r") as count_file:
        count = 0
        try:
            count = int(count_file.readline())
        except ValueError:
            logger.info("Invalid count file: {}".format(count_filename))
        finally:
            return count


def get_spritesheet_and_count_for_id_and_layer(phyto_c_id, layer):
    """Returns the path to the spritesheet containing all plant images for a given
    phytocoenosis ID and layer. If the file does not exist yet, it is generated.
    """

    filename = utils.get_full_texture_path(SPRITE_FILE.format(phyto_c_id, layer))

    logging.debug("Requested spritesheet for {}".format(filename))

    if not os.path.isfile(filename):
        logging.info("Generating spritesheet for {}...".format(filename))
        generate_spritesheet(phyto_c_id, layer)

    # If the file now exists, return it
    if os.path.isfile(filename):
        count = get_count(phyto_c_id, layer)
        return filename, count
    else:
        return None, None
