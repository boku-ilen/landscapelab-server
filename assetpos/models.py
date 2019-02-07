from django.contrib.gis.db import models
from raster.models import Tile


# TODO: is this a Layer?
class AssetType(models.Model):

    # an identifier string
    name = models.TextField()


# TODO: do we have to have an asset object for every asset? probably
class Asset(models.Model):

    # an identifier string
    name = models.TextField()


# this main table holds all the associated positions of the assets
# TODO: we have to optimize and probably cache it on the client as this will be called often
class AssetPositions(models.Model):

    # the associated tile (highest quality) where the
    tile = models.ForeignKey(Tile, on_delete=models.PROTECT)

    # the category of asset (e.g. Forest, Buildings, Lamps, etc)
    # TODO: we somewhere have to statically define them?
    asset_type = models.ForeignKey(AssetType, on_delete=models.PROTECT)

    # the actual asset (e.g. Pine, Lamp154, ...) which also could be a group of
    # TODO: how to parameterize (e.g. concrete height of tree, orientation?, ..)
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT)

    # the geographical location
    location = models.PointField()

    # the direction in degrees (0 = north) of the placement
    orientation = models.FloatField()
