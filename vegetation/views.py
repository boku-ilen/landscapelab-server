from django.http import JsonResponse

from vegetation.splatmap import get_splatmap_path_and_ids_for_coordinates
from vegetation.vegetation_distribution import get_distribution_for_id_and_layer
from vegetation.vegetation_spritesheet import get_spritesheet_and_count_for_id_and_layer


def get_vegetation_splatmap(request, meter_x, meter_y):
    """Returns a JsonResponse with the path to the splatmap PNG for the given location"""

    splat_path, ids = get_splatmap_path_and_ids_for_coordinates(int(float(meter_x)), int(float(meter_y)))

    res = {
        'path_to_splatmap': splat_path,
        'ids': ids
    }

    return JsonResponse(res)


def get_phytocoenosis_data(request, phytocoenosis_id, layer_name):
    """Returns a JsonResponse with the path to the distribution graphic and the path to the spritesheet for a given
    phytocoenosis at a given layer.
    """

    spritesheet, count = get_spritesheet_and_count_for_id_and_layer(phytocoenosis_id, layer_name)

    res = {
        'path_to_distribution': get_distribution_for_id_and_layer(phytocoenosis_id, layer_name),
        'path_to_spritesheet': spritesheet,
        'number_of_sprites': count
    }

    return JsonResponse(res)