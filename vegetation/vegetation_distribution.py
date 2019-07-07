import logging
import os

from landscapelab import utils

DISTRIBUTION_BASE = "phytocoenosis-distribution/"
DISTRIBUTION_PATHSET = os.path.join(DISTRIBUTION_BASE, "{}")
DISTRIBUTION_PATH = os.path.join(DISTRIBUTION_PATHSET, "{}.png")


def get_distribution_for_id_and_layer(pid, layer):
    """Returns the path to the spritesheet containing all plant images for a given phytocoenosis ID and layer.
    If the file does not exist yet, it is generated.
    """

    # FIXME solve circular dependency
    import vegetation.generate_distribution

    filename = utils.get_full_texture_path(DISTRIBUTION_PATH.format(pid, layer))

    if not os.path.isfile(filename):
        logging.info("Generating distribution for {}...".format(filename))
        vegetation.generate_distribution.generate_distribution_for_phytocoenosis_and_layer(pid, layer)

    # If the file now exists, return it
    if os.path.isfile(filename):
        return utils.replace_path_prefix(filename)
