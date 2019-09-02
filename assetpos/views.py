import logging
import webmercator

from django.contrib.gis import geos
from django.db.models import Q
from django.http import JsonResponse

from assetpos.models import AssetType, AssetPositions, Asset
from assetpos.models import Tile
from django.contrib.gis.geos import Polygon

logger = logging.getLogger(__name__)


def get_squared_distance(point1, point2):
    """Returns the distance between two points squared (for efficiency)"""
    return (point1.x - point2.x) ** 2 + (point1.y - point2.y) ** 2


def can_place_at_position(assettype, meter_x, meter_y):
    """Returns true if the asset with the given id may be placed at the given position."""

    position = geos.Point(float(meter_x), float(meter_y))

    placement_areas = assettype.placement_areas

    # if there is another asset closer to this one than the minimum distance, it may not be placed
    if assettype.minimum_distance != 0:
        for other_asset in AssetPositions.objects.filter(asset_type_id=assettype).all():
            squared_distance = get_squared_distance(other_asset.location, position)
            required_squared_distance = assettype.minimum_distance ** 2

            if squared_distance < required_squared_distance:
                return not assettype.allow_placement

    # if there are no placement areas present this asset can be placed according
    # to it's global setting
    if not placement_areas:
        return assettype.allow_placement

    # check if the position and the placement areas overlap
    if placement_areas.covers(position):
        return assettype.allow_placement
    else:
        return not assettype.allow_placement


def register_assetposition(request, asset_id, meter_x, meter_y, orientation=0):
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

    # TODO: handling the default orientation is up to the client
    new_assetpos = AssetPositions(location=location_point, orientation=orientation,
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
        asset_count = len(AssetPositions.objects.filter(asset_type=2).all())\
                      + len(AssetPositions.objects.filter(asset_type=3).all())

    ret["number_of_assets"] = asset_count
    ret["total_energy_contribution"] = asset_count * 10  # TODO: Placeholder energy contribution

    return JsonResponse(ret)


# returns all assets of a given type within the extent of the given tile
# TODO: add checks
# TODO: add additional properties (eg. overlay information)
def get_assetpositions(request, zoom, tile_x, tile_y, assettype_id):
    ret = {
        "assets": {}
    }

    # Construct the polygon which represents this tile, filter assets with that polygon
    point = webmercator.Point(meter_x=float(tile_x), meter_y=float(tile_y), zoom_level=int(zoom))
    tile_center = webmercator.Point(tile_x=point.tile_x, tile_y=point.tile_y, zoom_level=int(zoom))

    polygon = Polygon((
        (tile_center.meter_x + tile_center.meters_per_tile / 2, tile_center.meter_y + tile_center.meters_per_tile / 2),
        (tile_center.meter_x + tile_center.meters_per_tile / 2, tile_center.meter_y - tile_center.meters_per_tile / 2),
        (tile_center.meter_x - tile_center.meters_per_tile / 2, tile_center.meter_y - tile_center.meters_per_tile / 2),
        (tile_center.meter_x - tile_center.meters_per_tile / 2, tile_center.meter_y + tile_center.meters_per_tile / 2),
        (tile_center.meter_x + tile_center.meters_per_tile / 2, tile_center.meter_y + tile_center.meters_per_tile / 2)))

    assets = AssetPositions.objects.filter(asset_type=AssetType.objects.get(id=assettype_id),
                                           location__contained=polygon).all()

    ret["assets"] = {asset.id: {"position": [asset.location.x, asset.location.y], "modelpath": asset.asset.name}
                     for asset in assets}

    return JsonResponse(ret, safe=False)


# gets the attributes and values of the requested asset_id
def get_attributes(request, asset_id):

    ret = {}
    asset = Asset.objects.get(id=asset_id)
    for attribute in asset.attributes:
        ret[attribute.property.identfier] = attribute.value

    return JsonResponse(ret)


# lists all asset types and nest the associated assets and provide
# the possibility to filter only editable asset types
def getall_assettypes(request, editable=False):

    ret = {}

    # get the relevant asset types
    if not editable:
        asset_types = AssetType.objects.all()
    else:
        asset_types = AssetType.objects.filter(Q(allow_placement=True) |
                                               Q(placement_areas__isnull=False))

    # get the assets of each asset types and build the json result
    for asset_type in asset_types:
        assets = Asset.objects.filter(asset_type=asset_type)
        assets_json = {}
        for asset in assets:
            assets_json[asset.id] = {
                'name': asset.name,
            }
        ret[asset_type.id] = {
            'name': asset_type.name,
            'allow_placement': asset_type.allow_placement,
            'placement_areas': asset_type.placement_areas.json,  # FIXME: maybe we need to seperate each polygon
            'display_radius': asset_type.display_radius,
            'assets': assets_json
        }

    return JsonResponse(ret)
