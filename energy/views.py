from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist

from assetpos.models import AssetPositions, AssetType
from energy.models import EnergyTargets, AssetpositionToEnergylocation, EnergyLocation


# retrieves and returns the current placed energy values for the given scenario
# and returns it as json for the energy detail page in the client
def get_energy_contribution(request, scenario_id, asset_type_id=None):
    """Returns a json response with the energy contribution and number of contributing
     assets, either for a given asset type or for all editable assets."""

    scenario_id = int(scenario_id)
    if asset_type_id:
        asset_type_id = int(asset_type_id)

    ret = {
        "total_energy_contribution": 0,
        "number_of_assets": 0
    }

    # calculate the energy and asset count for the given asset_type
    if asset_type_id:
        asset_count = AssetPositions.objects.filter(asset_type=asset_type_id, tile__scenario_id=scenario_id).count()
        asset_energy_total = get_energy_by_scenario(scenario_id, asset_type_id)

    # calculate asset_count and asset_energy_total for all editable asset types
    else:
        asset_count = 0
        asset_energy_total = 0
        for editable_asset_type in get_all_editable_asset_types():
            asset_count += AssetPositions.objects.filter(asset_type=editable_asset_type.id,
                                                         tile__scenario_id=scenario_id).count()
            asset_energy_total += get_energy_by_scenario(scenario_id, asset_type_id)

    # return the calculated values in json
    ret["number_of_assets"] = asset_count
    ret["total_energy_contribution"] = asset_energy_total
    return JsonResponse(ret)


# does the acutal calculation to get the energy production for a scenario with
# an optional given asset type
def get_energy_by_scenario(scenario_id, asset_type_id=None):

    energy_sum = 0

    # recursively get all energy values if no asset_type is given
    if not asset_type_id:
        for editable_asset_type in get_all_editable_asset_types():
            energy_sum += get_energy_by_scenario(scenario_id, editable_asset_type.pk)

    else:
        # get all asset positions of this asset_type in our scenario
        asset_positions = AssetPositions.objects.filter(asset_type_id=asset_type_id, tile__scenario_id=scenario_id).all()
        for asset_position in asset_positions:
            energy_sum += get_energy_by_location(asset_position.pk)

    return energy_sum


# this wraps the numerical answer in a json response for the web request
def get_json_energy_by_location(request, asset_position_id):
    asset_position_id = int(asset_position_id)
    return JsonResponse({"energy_production": get_energy_by_location(asset_position_id)})


# calculates the energy production of a specific placed asset (asset position) and returns -1
# if the calculation fails
def get_energy_by_location(asset_position_id):

    try:
        asset_position = AssetPositions.objects.get(pk=asset_position_id)
    except ObjectDoesNotExist:
        return -1

    try:
        position2energy = AssetpositionToEnergylocation.objects.get(asset_position=asset_position)
    except ObjectDoesNotExist:
        # if the association table does not exist do the actual lookup
        try:
            energy_location = EnergyLocation.objects.get(polygon__contains=asset_position.location,
                                                         asset_type=asset_position.asset_type)

            position2energy = AssetpositionToEnergylocation()
            position2energy.asset_position = asset_position
            position2energy.energy_location = energy_location
            position2energy.save()
        except ObjectDoesNotExist:
            return -1

    energy_production = position2energy.energy_location.energy_production
    return energy_production


def get_all_editable_asset_types():

    # get all editable assets_types
    editable_asset_types = []
    for asset_type in AssetType.objects.all():
        if not asset_type.placement_areas:
            if asset_type.allow_placement:
                editable_asset_types.append(asset_type)
        else:
            editable_asset_types.append(asset_type)

    return editable_asset_types


# returns the energy target for a scenario and optionally filtered for a specific asset_type
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


# wraps the get_energy_targets method in a json answer
def get_json_energy_target(request, scenario_id, asset_type_id):
    scenario_id = int(scenario_id)
    asset_type_id = int(asset_type_id)
    return JsonResponse({"energy_target": get_energy_targets(scenario_id, asset_type_id)})
