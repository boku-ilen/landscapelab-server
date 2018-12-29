from django.contrib.gis.db import models

from location.models import Scenario


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

    # TODO: decide if we want to store the raster data itself into the database or just
    # TODO: a pointer to the filename which can then be received with a direct read from a file ?


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
