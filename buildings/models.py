from django.contrib.gis.db import models
from django.contrib.gis.geos import Polygon, LinearRing
from assetpos.models import AssetPositions


class BuildingLayout(models.Model):
    asset = models.ForeignKey(AssetPositions, on_delete=models.CASCADE)

    # the vertices of the building layout relative to the position
    vertices = models.PolygonField(srid=4326, default=Polygon(LinearRing([
        (-1, -1),
        (1, -1),
        (1, 1),
        (-1, 1),
        (-1, -1)
    ])))

    def __str__(self):
        return "{} ({})".format(self.asset.asset.name, str(self.position))  # FIXME: position not found?
