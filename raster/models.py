from django.contrib.gis.db import models

from location.models import Scenario


# this represents a tile in a LOD pyramid (?)
class Tile(models.Model):

    # the associated project area
    project = models.ForeignKey(Scenario, on_delete=models.PROTECT)

    # TODO: decide if we want to store the raster data itself into the database or just
    # a pointer to the filename which can then be received with a direct read from a file ?
