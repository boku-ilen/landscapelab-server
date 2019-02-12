from django.http import JsonResponse

from vegetation_spritesheet import generate_spritesheet


def get_vegetation_splatmap(request, meter_x, meter_y):
    """Returns a JsonResponse with the path to the splatmap PNG for the given location"""

    res = {
        'path_to_splatmap': ''
    }

    return JsonResponse(res)


def get_phytocoenosis_data(request, phytocoenosis_id, layer_name):
    """Returns a JsonResponse with the path to the distribution graphic and the path to the spritesheet for a given
    phytocoenosis at a given layer. """

    res = {
        'path_to_distribution': '',
        'path_to_spritesheet': generate_spritesheet(phytocoenosis_id, layer_name)
    }

    return JsonResponse(res)
