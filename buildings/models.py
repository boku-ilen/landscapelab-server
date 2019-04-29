from django.conf import settings
from django.contrib.gis.db import models
from assetpos.models import AssetPositions


# stores building footprint data associated with a building asset
class BuildingFootprint(models.Model):

    # the associated asset with this footprint
    asset = models.ForeignKey(AssetPositions, on_delete=models.PROTECT)

    # the vertices of the building layout relative to the position
    vertices = models.PolygonField(srid=settings.DEFAULT_SRID)

    # the height of the building in meters
    height = models.FloatField(default=0)
