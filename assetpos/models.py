from django.conf import settings
from django.contrib.gis.db import models
from raster.models import Tile


# an asset type is a collection of common assets which share some properties
# especially currently they share the same placement configuration
class AssetType(models.Model):

    # an identifier string
    name = models.TextField()

    # FIXME: we consider moving the placement configuration to class Asset
    # FIXME: also we probably have to make this configurable per scenario!
    # multiple polygons which, depending on the parameter allow_placement are the forbidden or the allowed
    # areas where this type of object can be placed .. if this parameter is null there are non such areas
    # and the allow_placement globally allows or disallows the placement of this type
    placement_areas = models.MultiPolygonField(null=True, srid=settings.DEFAULT_SRID)

    # if True it is globally allowed to place this element, the placement_areas are forbidden areas
    # if False it is not allowed to place this element, the placement_areas are zones where it is allowed
    allow_placement = models.BooleanField(default=False)

    # this is the radius around the 1st person player in the client where this asset type is to be displayed
    # the default setting of 0 means unlimited
    display_radius = models.IntegerField(default=0)

    # the minimum distance that this asset needs to have to other assets of its type - not allowed
    # to be placed if it's too close
    minimum_distance = models.IntegerField(default=0)

    # if True, this asset type is not handled in the usual asset pipeline but has other functionality
    abstract = models.BooleanField(default=False)

    # the target energy for this asset type
    energy_target = models.IntegerField(default=0)


class Property(models.Model):

    # an identifier for the property
    identifier = models.TextField()

    # the associated asset type
    asset_type = models.ForeignKey(AssetType, on_delete=models.PROTECT)


# an Asset is directly linked to one specific 3d model in the client
class Asset(models.Model):

    # an identifier string
    name = models.TextField()

    # the category of the asset
    asset_type = models.ForeignKey(AssetType, on_delete=models.PROTECT)

    # if True, only one AssetPosition can be associated with this Asset at a time
    # TODO: Can we enforce this in the database itself? Currently, only the 'create' request complies with this
    unique = models.BooleanField(default=False)


class Attribute(models.Model):

    # the asset to which the given key/value pair is associated
    asset = models.ForeignKey(Asset, related_name="attributes", on_delete=models.PROTECT)

    # the associated property
    property = models.ForeignKey(Property, on_delete=models.PROTECT)

    # the associated numeric value
    # TODO: is there a case for a string value?
    value = models.FloatField()


# this main table holds all the instances of assets with their location
# TODO: we have to optimize and probably cache it on the client as this will be called often
class AssetPositions(models.Model):

    # the associated tile (highest quality)
    # nullable for dynamic assets which are not bound to a specific tile
    tile = models.ForeignKey(Tile, on_delete=models.SET_NULL, null=True)

    # the category of asset (e.g. Forest, Buildings, Lamps, etc)
    # TODO: can we get them via asset?
    asset_type = models.ForeignKey(AssetType, on_delete=models.PROTECT)

    # the actual asset (e.g. Pine, Lamp154, ...) which also could be a group of
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT)

    # the geographical location
    location = models.PointField(srid=settings.DEFAULT_SRID)

    # the direction in degrees (0 = north) of the placement
    orientation = models.FloatField(default=0)
