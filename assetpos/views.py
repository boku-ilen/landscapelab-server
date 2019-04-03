import logging

from django.contrib.gis.geos import Point
from django.http import JsonResponse, HttpResponse
from assetpos.models import AssetType, Tile, AssetPositions, Asset
from buildings.views import generate_buildings_with_asset_id
from django.contrib.staticfiles import finders

from placement_validation import can_place_at_position

logger = logging.getLogger(__name__)


def register_assetposition(request, asset_id, meter_x, meter_y):
    """Called when an asset should be instantiated at the given location.
    Returns a JsonResponse with 'creation_success' (bool) and, if true, the 'assetpos_id' of the new assetpos.
    """

    ret = {
        "creation_success": False,
        "assetpos_id": None
    }

    if not Asset.objects.filter(id=asset_id).exists():
        return JsonResponse(ret)
    asset = Asset.objects.get(id=asset_id)

    assettype = asset.asset_type

    if not can_place_at_position(assettype, meter_x, meter_y):
        return JsonResponse(ret)
    location_point = Point(float(meter_x), float(meter_y))

    new_assetpos = AssetPositions(location=location_point, orientation=1, tile_id=1, asset=asset, asset_type=assettype)
    new_assetpos.save()

    ret["creation_success"] = True
    ret["assetpos_id"] = new_assetpos.id

    return JsonResponse(ret)


def remove_assetposition(request, assetpos_id):
    """Removes the asset instance (assetpos) with the given id from the database.
    Returns a JsonResponse with 'delete_success' (bool)."""

    ret = {
        "delete_success": False
    }

    assetpos = AssetPositions.objects.filter(id=assetpos_id)

    if not assetpos.exists():
        return JsonResponse(ret)

    assetpos.delete()
    ret["delete_success"] = True

    return JsonResponse(ret)


def get_assetposition(request, assetpos_id):
    """Returns a JsonResponse with the 'position' of the asset instance at the given id."""

    ret = {
        "position": None
    }

    if not AssetPositions.objects.filter(id=assetpos_id).exists():
        return JsonResponse(ret)
    assetpos = AssetPositions.objects.get(id=assetpos_id)

    ret["position"] = [assetpos.location.x, assetpos.location.y]

    return JsonResponse(ret)


def set_assetposition(request, assetpos_id, meter_x, meter_y):
    """Sets the position of an existing asset instance with the given id to the given coordinates.
    Returns a JsonResponse with 'success' (bool). If the asset does not exist or can't be moved to that position, this
    'success' is False."""

    ret = {
        "success": False
    }

    if not AssetPositions.objects.filter(id=assetpos_id).exists():
        return JsonResponse(ret)
    assetpos = AssetPositions.objects.get(id=assetpos_id)

    if not can_place_at_position(assetpos.asset_type, meter_x, meter_y):
        return JsonResponse(ret)

    assetpos.location = Point(float(meter_x), float(meter_y))
    assetpos.save()

    ret["success"] = True

    return JsonResponse(ret)


# returns all assets of a given type within the extent of the given tile
# TODO: add checks
# TODO: add additional properties (eg. overlay information)
def get_assetpositions(request, zoom, tile_x, tile_y, assettype_id):

    # fetch all associated assets
    asset_type = AssetType.objects.get(id=assettype_id)
    tile = Tile.objects.get(lod=zoom, x=tile_x, y=tile_y)
    assets = AssetPositions.objects.filter(tile=tile, asset_type=asset_type)

    # create the return dict
    ret = []
    gen_buildings = []
    for asset_position in assets:
        if asset_type.name == 'building':
            found_file = finders.find("{}.dae".format(asset_position.asset.name))
            if not found_file: # os.path.isfile(found_file):
                gen_buildings.append(asset_position.id)

        x,y = asset_position.location
        ret.append({'x': x, 'y': y, 'asset': asset_position.asset.name})

    if gen_buildings:
        generate_buildings_with_asset_id(gen_buildings)

    return JsonResponse(ret, safe=False)
