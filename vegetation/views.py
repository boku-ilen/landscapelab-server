from django.http import JsonResponse

from vegetation import generate_distribution, splatmap, phytocoenosis_textures, vegetation_spritesheet


def get_vegetation_splatmap(request, meter_x, meter_y, zoom):
    """Returns a JsonResponse with the path to the splatmap PNG for the given location"""

    zoom = int(zoom)
    splat_path, ids = splatmap.get_splatmap_path_and_ids_for_coordinates(float(meter_x), float(meter_y), zoom)

    res = {
        'path_to_splatmap': splat_path,
        'ids': ids
    }

    return JsonResponse(res)


def get_phytocoenosis_data(request, phyto_c_id, layer_name):
    """Returns a JsonResponse with the path to the distribution graphic and the path to the
    spritesheet for a given phytocoenosis at a given layer.

    All available detail ground texture paths (albedo_path, bumpmap_path, heightmap_detail_path)
    are included as well."""

    spritesheet, count = vegetation_spritesheet.get_spritesheet_and_count_for_id_and_layer(phyto_c_id, layer_name)

    res = {
        'path_to_distribution': generate_distribution.get_distribution_for_id_and_layer(phyto_c_id, layer_name),
        'path_to_spritesheet': spritesheet,
        'number_of_sprites': count,
        'distribution_pixels_per_meter': generate_distribution.PIXELS_PER_METER
    }

    # Add available detail ground textures to the dictionary
    res.update(phytocoenosis_textures.get_all_ground_texture_paths(phyto_c_id))

    return JsonResponse(res)
