from django.http import JsonResponse

from assetpos.models import AssetPositions


def get_energy_contribution(request, asset_type_id=None):
    """Returns a json response with the energy contribution and number of contributing
     assets, either for a given asset type or for all assets."""

    ret = {
        "total_energy_contribution": 0,
        "number_of_assets": 0
    }

    if asset_type_id:
        asset_count = len(AssetPositions.objects.filter(asset_type=asset_type_id).all())
    else:
        # TODO: If we get all, Buildings are included, so the IDs are hardcoded for this placeholder
        #  We may need an additional field (or model?) for energy contributing assets in the future
        asset_count = len(AssetPositions.objects.filter(asset_type=2).all()) \
                      + len(AssetPositions.objects.filter(asset_type=3).all())

    ret["number_of_assets"] = asset_count
    ret["total_energy_contribution"] = asset_count * 10  # TODO: Placeholder energy contribution

    return JsonResponse(ret)
