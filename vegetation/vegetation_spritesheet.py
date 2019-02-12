import os

from django.shortcuts import get_object_or_404

import settings
from vegetation.models import Phytocoenosis
from PIL import Image

SPRITE_FILE = settings.STATICFILES_DIRS[0] + "/phytocoenosis-spritesheet/{}/{}.png"


def generate_spritesheet(id, layer):
    """Generates the spritesheet with all plant images for a given phytocoenosis ID and layer."""
    sprite_paths = get_object_or_404(Phytocoenosis, id=id).speciesRepresentations.billboard

    sprites = map(Image.open, list(sprite_paths))
    widths, heights = zip(*(s.size for s in sprites))

    max_width = max(widths)
    max_height = max(heights)

    spritesheet = Image.new('RGB', (max_width * len(sprite_paths), max_height))

    x_offset = 0

    for sprite in sprites:
        spritesheet.paste(sprite, (x_offset, 0))
        x_offset += max_width

    spritesheet.save(SPRITE_FILE.format(id, layer))


def get_spritesheet_for_id_and_layer(id, layer):
    """Returns the path to the spritesheet containing all plant images for a given phytocoenosis ID and layer.
    If the file does not exist yet, it is generated.
    """

    filename = SPRITE_FILE.format(id, layer)

    if not os.path.isfile(filename):
        generate_spritesheet(id, layer)

    return filename
