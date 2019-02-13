import logging
import os

from django.shortcuts import get_object_or_404

import settings
from vegetation.models import Phytocoenosis
from PIL import Image

SPRITE_BASEPATH = settings.STATICFILES_DIRS[0] + "/phytocoenosis-spritesheet/"
SPRITE_PATHSET = settings.STATICFILES_DIRS[0] + "/phytocoenosis-spritesheet/{}"
SPRITE_FILE = settings.STATICFILES_DIRS[0] + "/phytocoenosis-spritesheet/{}/{}.png"

logger = logging.getLogger(__name__)


def generate_spritesheet(id, layer):
    """Generates the spritesheet containing all plant images for a given phytocoenosis ID and layer.

    Example: With id=2 and layer=K, the resulting path would be /phytocoenosis-spritesheet/2/K.png
    """

    # TODO: Layer is not actually used yet!
    representations = get_object_or_404(Phytocoenosis, id=id).speciesRepresentations.all()
    sprite_paths = [rep.billboard for rep in representations]

    # Open all sprites at the sprite_paths using Pillow
    sprites = list(map(Image.open, sprite_paths))
    widths, heights = zip(*(s.size for s in sprites))

    # The maximum width and height are used for the spritesheet in order to fit in all images
    max_width = max(widths)
    max_height = max(heights)

    spritesheet = Image.new('RGBA', (max_width * len(sprite_paths), max_height))

    # Iterate over all sprites and paste them in the spritesheet, with an increasing x_offset, at the correct height
    # to have every sprite reach the bottom of the image
    x_offset = 0

    for sprite in sprites:
        width, height = sprite.size
        spritesheet.paste(sprite, (x_offset, max_height - height))
        x_offset += max_width

    # Create all required directories if they don't yet exist
    pathset = SPRITE_PATHSET.format(id)

    if not (os.path.exists(SPRITE_BASEPATH)):
        os.mkdir(SPRITE_BASEPATH)

    if not (os.path.exists(pathset)):
        os.mkdir(pathset)

    # Save the spritesheet
    filename = SPRITE_FILE.format(id, layer)
    spritesheet.save(filename)

    logging.info("Sprite saved into {}".format(filename))


def get_spritesheet_for_id_and_layer(id, layer):
    """Returns the path to the spritesheet containing all plant images for a given phytocoenosis ID and layer.
    If the file does not exist yet, it is generated.
    """

    filename = SPRITE_FILE.format(id, layer)

    logging.info("Requested spritesheet for {}".format(filename))

    if not os.path.isfile(filename):
        logging.info("Generating spritesheet for {}...".format(filename))
        generate_spritesheet(id, layer)

    return filename
