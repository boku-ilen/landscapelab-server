import logging
import webmercator

from django.contrib.gis import geos
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from django.db.models import Q
from django.http import JsonResponse

from assetpos.models import AssetType, AssetPositions, Asset
from django.contrib.gis.geos import Polygon

from assetpos import util
from location.models import Scenario
from raster.tiles import get_root_tile

logger = logging.getLogger(__name__)

MAX_ASSETS_PER_RESPONSE = 30


def can_place_at_position(assettype, meter_x, meter_y):
    """Returns true if the asset with the given id may be placed at the given position."""

    position = geos.Point(float(meter_x), float(meter_y))

    placement_areas = assettype.placement_areas

    # if there is another asset closer to this one than the minimum distance, it may not be placed
    if assettype.minimum_distance != 0:
        # TODO: We might want to filter by scenario here as well, otherwise assets from other
        #  scenarios can block this one
        # TODO: This can be done much more efficiently using a spatial filter and checking if the count is 0
        for other_asset in AssetPositions.objects.filter(asset_type_id=assettype).all():
            squared_distance = util.get_squared_distance(other_asset.location, position)
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


# TODO: Remove default scenario_id=10 once the old request isn't used anymore
def register_assetposition(request, asset_id, meter_x, meter_y, orientation=0, scenario_id=10):
    """Called when an asset should be instantiated at the given location.
    Returns a JsonResponse with 'creation_success' (bool) and, if true, the
    'assetpos_id' of the new assetpos."""

    ret = {
        "creation_success": False,
        "assetpos_id": None
    }

    if not Scenario.objects.filter(id=scenario_id):
        logger.warn("Non-existent scenario with ID {} requested!".format(scenario_id))
        return JsonResponse(ret)

    scenario = Scenario.objects.get(id=scenario_id)

    if not Asset.objects.filter(id=asset_id).exists():
        logger.warn("Attempt to create instance of on-existent asset with ID {}!".format(asset_id))
        return JsonResponse(ret)

    asset = Asset.objects.get(id=asset_id)

    assettype = asset.asset_type

    # If the ignore_placement_restrictions flag is not set and the asset may not be placed here, return
    if (not asset.ignore_placement_restrictions) and (not can_place_at_position(assettype, meter_x, meter_y)):
        return JsonResponse(ret)

    location_point = geos.Point(float(meter_x), float(meter_y))

    # TODO: handling the default orientation is up to the client
    new_assetpos = AssetPositions(location=location_point, orientation=orientation,
                                  asset=asset, asset_type=assettype, tile=get_root_tile(scenario))

    # If this is a unique asset, there should only be one instance -> delete existing position first
    # TODO: Is there a cleaner way for this? (See TODO in assetpos/models.py at the 'unique' field)
    if asset.unique:
        existing = AssetPositions.objects.filter(asset_type=assettype, asset=asset)

        if existing.exists():
            existing.delete()

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


def get_near_assetpositions(request, asset_or_assettype_id, meter_x, meter_y, by_assettype=False):
    """Returns all AssetPositions of a given Asset-ID or AssetType-ID (if by_assettype == True) which are
    closer than the AssetType's display_radius to the given point.
    If the display_radius is 0, all AssetPositions are returned.
    """

    meter_x = float(meter_x)
    meter_y = float(meter_y)
    asset_or_assettype_id = int(asset_or_assettype_id)

    ret = {}

    if by_assettype:
        # Request by AssetType -> Get all AssetPositions with that AssetType
        if not AssetType.objects.filter(id=asset_or_assettype_id).exists():
            logger.warn("AssetType with given ID {} does not exist!".format(asset_or_assettype_id))
            return ret

        asset_type = AssetType.objects.get(id=asset_or_assettype_id)
        objects = AssetPositions.objects.filter(asset_type=asset_type)
    else:
        # Request by Asset -> Get all AssetPositions of that Asset
        if not Asset.objects.filter(id=asset_or_assettype_id).exists():
            logger.warn("Asset with given ID {} does not exist!".format(asset_or_assettype_id))
            return ret

        asset = Asset.objects.get(id=asset_or_assettype_id)
        asset_type = asset.asset_type
        objects = AssetPositions.objects.filter(asset=asset)

    # Create a circle which the visible objects overlap with
    center = geos.Point(meter_x, meter_y, srid=3857)
    radius = asset_type.display_radius

    if radius > 0:
        # If the radius is > 0, we have to only return the nearby objects; the dwithin query is optimized for this
        near_assetpositions = objects.filter(location__dwithin=(center, D(m=radius))) \
            .annotate(distance=Distance("location", center)) \
            .order_by("distance")
    else:
        # If the radius is 0, this means that there is no limit -> Return all
        near_assetpositions = objects.all()

    number_of_assets = len(near_assetpositions)

    if number_of_assets > MAX_ASSETS_PER_RESPONSE:
        returned_assetpositions = near_assetpositions[0:MAX_ASSETS_PER_RESPONSE]
    else:
        returned_assetpositions = near_assetpositions

    ret["assets"] = {assetposition.id: {"position": [assetposition.location.x, assetposition.location.y],
                                        "asset_id": assetposition.asset_id,
                                        "asset_name": assetposition.asset.name,
                                        "distance": str(assetposition.distance)}
                     for assetposition in returned_assetpositions}

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


def get_assettypes(editable=False, include_abstract=False):
    if not editable:
        asset_types = AssetType.objects.all()
    else:
        # Editable asset types have allow_placement=True or allow_placement=False, but with placement_areas as
        #  exceptions.
        asset_types = AssetType.objects.filter(Q(allow_placement=True) |
                                               Q(placement_areas__isnull=False))

    # Don't include abstract assets unless the include_abstract parameter is True
    if not include_abstract:
        asset_types = asset_types.filter(abstract=False)

    return asset_types


# lists all asset types and nest the associated assets and provide
# the possibility to filter only editable asset types
# By default, abstract assets are excluded since those are placed by special mechanisms.
# FIXME: we would need to filter per scenario
def getall_assettypes(request, editable=False, include_abstract=False):
    ret = {}

    # get the relevant asset types
    asset_types = get_assettypes(editable, include_abstract)

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
            # FIXME: maybe we need to seperate each polygon
            'placement_areas': asset_type.placement_areas.coords if asset_type.placement_areas else None,
            'display_radius': asset_type.display_radius,
            'assets': assets_json
        }

    return JsonResponse(ret)
