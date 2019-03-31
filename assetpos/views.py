import logging

from django.contrib.gis.geos import Point
from django.http import JsonResponse, HttpResponse
from assetpos.models import AssetType, Tile, AssetPositions, Asset
from buildings.views import generate_buildings_with_asset_id
from django.contrib.staticfiles import finders

logger = logging.getLogger(__name__)


# sets the position of an existing asset to given values
# FIXME: this is a draft version - probably won't work out of the box
def set_assetposition(request, asset_id, meters_x, meters_y):

    # TODO: check permissions? & validate?
    asset = Asset.objects.get(id=asset_id)
    asset_position = AssetPositions.objects.filter(asset=asset)
    coordinates = Point(float(meters_x), float(meters_y))
    asset_position.location = coordinates
    asset_position.save()

    return HttpResponse(status=200)


# returns all assets of a given type within the extent of the given tile
# TODO: add checks
# TODO: add additional properties (eg. overlay information)
def get_assetposition(request, zoom, tile_x, tile_y, assettype_id):

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
