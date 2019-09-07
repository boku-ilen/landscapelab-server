from django.http import JsonResponse

from assetpos.models import AssetPositions, AssetType
from energy.models import EnergyTargets


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
        # calculate asset_count and asset_energy_total for all editable asset types
        asset_count = 0
        asset_energy_total = 0
        for editable_asset_type in get_all_editable_asset_types():
            asset_count += len(AssetPositions.objects.filter(asset_type=editable_asset_type.id).all())
            asset_energy_total += get_energy_by_scenario(request, scenario_id, asset_type_id)

    # return the calculated values in json
    ret["number_of_assets"] = asset_count
    ret["total_energy_contribution"] = asset_energy_total
    return JsonResponse(ret)


def get_energy_by_scenario(request, scenario_id, asset_type_id=None):

    energy_sum = 0

    # recursively get all energy values if no asset_type is given
    if not asset_type_id:
        for editable_asset_type in get_all_editable_asset_types():
            energy_sum += get_energy_by_scenario(request, scenario_id, editable_asset_type)

    else:
        # get all asset positions of this asset_type in our scenario
        asset_positions = AssetPositions.objects.filter()
        for asset_position in asset_positions:
            energy_sum += get_energy_by_location(request, asset_position.id)

    return energy_sum


def get_energy_by_location(request, asset_position_id):

    return 0


def get_all_editable_asset_types():

    # get all editable assets_types
    editable_asset_types = []
    for asset_type in AssetType.objects.all():
        if not asset_type.placement_areas:
            if asset_type.allow_placement:
                editable_asset_types.append(asset_type)
        else:
            editable_asset_types.append(asset_type)

    return  editable_asset_types


def get_energy_targets(scenario_id, asset_type_id=None):

    energy_requirement_total = 0

    # change the filter for the entries based on a optionally provided asset_type_id
    if asset_type_id:
        energy_entries = EnergyTargets.objects.filter(scenario_id=scenario_id, asset_type_id=asset_type_id)
    else:
        energy_entries = EnergyTargets.objects.filter(scenario_id=scenario_id)

    # calculate the target energy value
    for energy_entry in energy_entries:
        energy_requirement_total += energy_entry.target_value

    return energy_requirement_total
