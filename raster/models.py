from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField

from location.models import Scenario


# the resolution of a tile in x and y
TILE_SIZE = 256


# this represents a tile in a LOD quadtree pyramid
class Tile(models.Model):

    # the associated project area (scenario)
    scenario = models.ForeignKey(Scenario, on_delete=models.PROTECT)

    # we add the actual quadtree structure
    # we might want to use https://django-mptt.readthedocs.io
    parent = models.ForeignKey('self', related_name='children', on_delete=models.PROTECT)

    # the level of detail identifier
    lod = models.IntegerField()

    # the x-coordinate in the quadtree pyramid
    x = models.BigIntegerField()

    # the y-coordinate in the quadtree pyramid
    y = models.BigIntegerField()

    # this is the heightmap of the give tile (None if not yet calculated)
    # stored as an 2 dimensional array of float values in meters (max. resolution 1cm)
    # TODO: how do we apply the different height modifications from other modules (roads, rivers, ..)
    # TODO: we can handle them by priority or store the entire calculation or geometries
    heightmap = ArrayField(ArrayField(models.FloatField(), size=TILE_SIZE), size=TILE_SIZE)


# all vectorized height information available (it is cut down based on a bounding box to the project extent)
class DigitalHeightModel(models.Model):

    # the tile on which the point is located
    # TODO: the tile is acutally also located on all parent tiles so we currently
    # TODO: need to insert the most detailed tile here
    tile = models.ForeignKey(Tile, on_delete=models.PROTECT)

    # the location of one data point
    point = models.PointField()

    # height in meters
    height = models.FloatField()

    # TODO: should we store the resolution too in a field so we can import multiple
    # TODO: resolutions for the same area and decide what to take later? but what
    # TODO: about different height information (inconsistencies between dhm sources?)
