import os

from django.conf import settings
from django.shortcuts import get_object_or_404

from vegetation.models import Phytocoenosis


def get_all_ground_texture_paths(pid):
    """Returns a dictionary with all available detail ground texture paths for the phytocoenosis at the requested ID.

    Format:
    {
        texture_name: path_to_texture
    }
    """

    phytocoenosis = get_object_or_404(Phytocoenosis, id=pid)
    tex_dict = {
        "albedo_path": os.path.join(settings.STATICFILES_DIRS[0], phytocoenosis.albedo_path) if phytocoenosis.albedo_path is not None else None,
        "normal_path": phytocoenosis.normal_path,
        "heightmap_detail_path": phytocoenosis.heightmap_detail_path
    }

    # Remove None values
    tex_dict = {k: v for k, v in tex_dict.items() if v}

    return tex_dict
