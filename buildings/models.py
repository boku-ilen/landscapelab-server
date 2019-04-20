from django.contrib.gis.db import models
from assetpos.models import AssetPositions


# stores building footprint data associated with a building asset
class BuildingFootprint(models.Model):

    # the associated asset with this footprint
    asset = models.ForeignKey(AssetPositions, on_delete=models.PROTECT)

    # the vertices of the building layout relative to the position
    vertices = models.PolygonField()

    # the height of the building in meters
    height = models.FloatField()

    # TODO add building height as a field

    # TODO: do we need this somewhere?
    # def __str__(self):
    #     return "{} ({})".format(self.asset.asset.name, str(self.position))  # FIXME: position not found?
