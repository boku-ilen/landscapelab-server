from django.contrib.gis.db import models
from django.contrib.gis.geos import Polygon, LinearRing
from assetpos.models import AssetPositions


# FIXME comment...
class BuildingFootprint(models.Model):

    # the associated asset with this footprint
    asset = models.ForeignKey(AssetPositions, on_delete=models.PROTECT)

    # the vertices of the building layout relative to the position
    vertices = models.PolygonField()


    # TODO: do we need this somewhere?
    # def __str__(self):
    #     return "{} ({})".format(self.asset.asset.name, str(self.position))  # FIXME: position not found?
