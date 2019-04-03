from django.contrib.gis.db import models
from raster.models import Tile


class AssetType(models.Model):

    # an identifier string
    name = models.TextField()

    # the areas within this type of asset can be placed
    placement_areas = models.MultiPolygonField()


class Property(models.Model):

    # an identifier for the property
    identfier = models.TextField()

    # the associated asset type
    asset_type = models.ForeignKey(AssetType, on_delete=models.PROTECT)


# TODO: do we have to have an asset object for every asset? probably
class Asset(models.Model):

    # an identifier string
    name = models.TextField()

    # the category of the asset
    asset_type = models.ForeignKey(AssetType, on_delete=models.PROTECT)


class Attribute(models.Model):

    # the asset to which the given key/value pair is associated
    asset = models.ForeignKey(Asset, related_name="attributes", on_delete=models.PROTECT)

    # the associated property
    property = models.ForeignKey(Property, on_delete=models.PROTECT)

    # the associated numeric value
    # TODO: is there a case for a string value?
    value = models.FloatField()


# this main table holds all the associated positions of the assets
# TODO: we have to optimize and probably cache it on the client as this will be called often
class AssetPositions(models.Model):

    # the associated tile (highest quality) where the
    tile = models.ForeignKey(Tile, on_delete=models.PROTECT)

    # the category of asset (e.g. Forest, Buildings, Lamps, etc)
    # TODO: can we get them via asset?
    asset_type = models.ForeignKey(AssetType, on_delete=models.PROTECT)

    # the actual asset (e.g. Pine, Lamp154, ...) which also could be a group of
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT)

    # the geographical location
    location = models.PointField()

    # the direction in degrees (0 = north) of the placement
    orientation = models.FloatField()
