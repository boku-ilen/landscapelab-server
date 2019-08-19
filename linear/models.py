from django.contrib.gis.db import models
from raster.models import Tile


# TODO: Some fields here overlap with assetpos. When we unify dynamic and static assets,
#  we can probably also have a common superclass for lines and assets!


# Specific categories for line data such as 'Farm Road' or 'Railroad'.
# Each LineType corresponds to one linear 3D definition in the client.
class LineType(models.Model):

    # A unique name for this type of line data, e.g. 'Motorway'
    name = models.TextField()

    # If a LineSegment has no specific width, this fallback is used
    width = models.FloatField()

    # The distance at which this type of line should be included in the response
    # The default of 0 means that all lines should always be included
    display_radius = models.IntegerField(default=0)


# A line segment is a geographical line with a specific type (e.g.
# a motorway), which belongs to a specific tile.
# The client draws the 3D definition according to the 'type' along
# the 'line' as soon as the 'tile' reaches a certain LOD.
class LineSegment(models.Model):

    # The actual data of the line segment
    line = models.LineStringField()

    # The tile which, ideally, the center of the line segment is in
    # TODO: Nullable since it's not yet sure whether this is really required
    tile = models.ForeignKey(Tile, null=True, on_delete=models.PROTECT)

    # The type which this line segment belongs to
    type = models.ForeignKey(LineType, on_delete=models.PROTECT)

    # Optional width if it deviates from the LineType default
    width = models.FloatField(null=True)
