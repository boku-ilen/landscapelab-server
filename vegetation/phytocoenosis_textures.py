from django.shortcuts import get_object_or_404

from landscapelab import utils
from vegetation.models import Phytocoenosis


def get_all_ground_texture_paths(pytho_c_id):
    """Returns a dictionary with all available detail ground texture paths
    for the phytocoenosis at the requested ID.

    Format:
    {
        texture_name: path_to_texture
    }
    """

    phytocoenosis = get_object_or_404(Phytocoenosis, id=pytho_c_id)

    albedo_path, normal_path, heightmap_detail_path = None, None, None
    if phytocoenosis.albedo_path:
        albedo_path = utils.get_full_texture_path(phytocoenosis.albedo_path)
    if phytocoenosis.normal_path:
        normal_path = utils.get_full_texture_path(phytocoenosis.normal_path)
    if phytocoenosis.heightmap_detail_path:
        heightmap_detail_path = utils.get_full_texture_path(phytocoenosis.heightmap_detail_path)

    tex_dict = {
        "albedo_path": utils.replace_path_prefix(albedo_path),
        "normal_path": utils.replace_path_prefix(normal_path),
        "heightmap_detail_path": utils.replace_path_prefix(heightmap_detail_path),
    }

    # Remove None values
    # TODO: why do we need to do this? The client should check for this..
    tex_dict = {k: v for k, v in tex_dict.items() if v}

    return tex_dict
