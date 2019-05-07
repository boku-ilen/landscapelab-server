import logging

from django.contrib.gis import geos
from django.http import JsonResponse
from django.contrib.staticfiles import finders

from assetpos.models import AssetType, Tile, AssetPositions, Asset
from buildings.views import generate_buildings_with_asset_id


logger = logging.getLogger(__name__)


def can_place_at_position(assettype, meter_x, meter_y):
    """Returns true if the asset with the given id may be placed at the given position."""

    placement_areas = assettype.placement_areas

    # if there are no placement areas present this asset can be placed according
    # to it's global setting
    if not placement_areas:
        return assettype.allow_placement

    # check if the position and the placement areas overlap
    position = geos.Point(meter_x, meter_y)
    if placement_areas.covers(position):
        return not assettype.allow_placement
    else:
        return assettype.allow_placement


def register_assetposition(request, asset_id, meter_x, meter_y):
    """Called when an asset should be instantiated at the given location.
    Returns a JsonResponse with 'creation_success' (bool) and, if true, the
    'assetpos_id' of the new assetpos."""

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
    location_point = geos.Point(float(meter_x), float(meter_y))

    # FIXME: hardcoded orientation - how do we want to set it by default?
    new_assetpos = AssetPositions(location=location_point, orientation=1,
                                  asset=asset, asset_type=assettype)
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


def get_assetpositions_global(request, asset_id):
    """Returns a JsonResponse with the 'position's of all asset instances of the given asset.
    The assets are named by their assetpos ID."""

    ret = {
        "assets": None
    }

    assets = AssetPositions.objects.filter(asset=asset_id).all()

    ret["assets"] = {asset.id: {"position": [asset.location.x, asset.location.y]} for asset in assets}

    return JsonResponse(ret)


def set_assetposition(request, assetpos_id, meter_x, meter_y):
    """Sets the position of an existing asset instance with the given id to the
    given coordinates. Returns a JsonResponse with 'success' (bool). If the asset
    does not exist or can't be moved to that position, this 'success' is False."""

    ret = {
        "success": False
    }

    if not AssetPositions.objects.filter(id=assetpos_id).exists():
        return JsonResponse(ret)
    assetpos = AssetPositions.objects.get(id=assetpos_id)

    if not can_place_at_position(assetpos.asset_type, meter_x, meter_y):
        return JsonResponse(ret)

    assetpos.location = geos.Point(float(meter_x), float(meter_y))
    assetpos.save()

    ret["success"] = True

    return JsonResponse(ret)


# returns all assets of a given type within the extent of the given tile
# TODO: add checks
# TODO: add additional properties (eg. overlay information)
# TODO: The result of this request should be structured the same as the
#  get_assetpositions_global result!
def get_assetpositions(request, zoom, tile_x, tile_y, assettype_id):

    # fetch all associated assets
    asset_type = AssetType.objects.get(id=assettype_id)
    tile = Tile.objects.get(lod=zoom, x=tile_x, y=tile_y)
    assets = AssetPositions.objects.filter(tile=tile, asset_type=asset_type)

    # create the return dict
    ret = []
    # FIXME: Why do we precalculate the buildings here? At least it should
    # FIXME: trigger a dedicated method somewhere in buildings?
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


# gets the attributes and values of the requested asset_id
def get_attributes(request, asset_id):

    ret = {}
    asset = Asset.objects.get(id=asset_id)
    for attribute in asset.attributes:
        ret[attribute.property.identfier] = attribute.value

    return JsonResponse(ret)


# lists all asset types and nest the associated assets and provide
# the posibility to filter only editable asset types
def getall_assettypes(request, editable=False):

    ret = {}

    return JsonResponse(ret)