import webmercator
from django.http import JsonResponse

from generate_distribution import PIXELS_PER_METER
from vegetation.phytocoenosis_textures import get_all_ground_texture_paths
from vegetation.splatmap import get_splatmap_path_and_ids_for_coordinates
from vegetation.vegetation_distribution import get_distribution_for_id_and_layer
from vegetation.vegetation_spritesheet import get_spritesheet_and_count_for_id_and_layer


def get_vegetation_splatmap(request, meter_x, meter_y, zoom):
    """Returns a JsonResponse with the path to the splatmap PNG for the given location"""

    zoom = int(zoom)
    p = webmercator.Point(meter_x=float(meter_x), meter_y=float(meter_y), zoom_level=zoom)
    splat_path, ids = get_splatmap_path_and_ids_for_coordinates(p.tile_x, p.tile_y, zoom)

    res = {
        'path_to_splatmap': splat_path,
        'ids': ids
    }

    return JsonResponse(res)


def get_phytocoenosis_data(request, phytocoenosis_id, layer_name):
    """Returns a JsonResponse with the path to the distribution graphic and the path to the spritesheet for a given
    phytocoenosis at a given layer.

    All available detail ground texture paths (albedo_path, bumpmap_path, heightmap_detail_path) are included as well.
    """

    spritesheet, count = get_spritesheet_and_count_for_id_and_layer(phytocoenosis_id, layer_name)

    res = {
        'path_to_distribution': get_distribution_for_id_and_layer(phytocoenosis_id, layer_name),
        'path_to_spritesheet': spritesheet,
        'number_of_sprites': count,
        'distribution_pixels_per_meter': PIXELS_PER_METER
    }

    # Add available detail ground textures to the dictionary
    res.update(get_all_ground_texture_paths(phytocoenosis_id))

    return JsonResponse(res)
