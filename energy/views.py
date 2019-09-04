from django.http import JsonResponse

from assetpos.models import AssetPositions, AssetType


def get_energy_contribution(request, scenario_id, asset_type_id=None):
    """Returns a json response with the energy contribution and number of contributing
     assets, either for a given asset type or for all editable assets."""

    ret = {
        "total_energy_contribution": 0,
        "number_of_assets": 0
    }

    if asset_type_id:
        asset_count = len(AssetPositions.objects.filter(asset_type=asset_type_id).all())
        asset_energy_total = get_energy_by_scenario(scenario_id, asset_type_id)

    else:

        # get all editable assets_types
        editable_asset_types = []
        for asset_type in AssetType.objects.all():
            if not asset_type.placement_areas:
                if asset_type.allow_placement:
                    editable_asset_types.append(asset_type)
            else:
                editable_asset_types.append(asset_type)

        # calculate asset_count and asset_energy_total for all editable asset types
        asset_count = 0
        asset_energy_total = 0
        for editable_asset_type in editable_asset_types:
            asset_count += len(AssetPositions.objects.filter(asset_type=editable_asset_type.id).all())
            asset_energy_total += get_energy_by_scenario(scenario_id, asset_type_id)

    # return the calculated values in json
    ret["number_of_assets"] = asset_count
    ret["total_energy_contribution"] = asset_energy_total
    return JsonResponse(ret)


def get_energy_by_scenario(request, scenario_id, asset_type_id=None):

    return 0


def get_energy_by_location(request, asset_position_id):

    return 0
