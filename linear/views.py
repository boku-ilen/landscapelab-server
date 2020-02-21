import webmercator
from django.contrib.gis import geos
from django.contrib.gis.geos import Polygon
from django.http import JsonResponse

from linear.models import LineType, LineSegment
import logging


def get_lines_for_tile(request, line_type_id, tile_x, tile_y, zoom):
    ret = {}

    line_type_id = int(line_type_id)

    # Construct the polygon which represents this tile, filter assets with that polygon
    point = webmercator.Point(meter_x=float(tile_x), meter_y=float(tile_y), zoom_level=int(zoom))
    tile_center = webmercator.Point(tile_x=point.tile_x, tile_y=point.tile_y, zoom_level=int(zoom))

    polygon = Polygon((
        (tile_center.meter_x + tile_center.meters_per_tile / 2, tile_center.meter_y + tile_center.meters_per_tile / 2),
        (tile_center.meter_x + tile_center.meters_per_tile / 2, tile_center.meter_y - tile_center.meters_per_tile / 2),
        (tile_center.meter_x - tile_center.meters_per_tile / 2, tile_center.meter_y - tile_center.meters_per_tile / 2),
        (tile_center.meter_x - tile_center.meters_per_tile / 2, tile_center.meter_y + tile_center.meters_per_tile / 2),
        (tile_center.meter_x + tile_center.meters_per_tile / 2, tile_center.meter_y + tile_center.meters_per_tile / 2)),
        srid=3857)

    segments = LineSegment.objects.filter(type=line_type_id, line__intersects=polygon)

    # Add the segments to the response
    for segment in segments.all():
        # Ensure WebMercator coordinates
        line = segment.line
        line.transform(3857)

        ret[segment.id] = {
            "line": line.coords,
            "width": segment.width}

    return JsonResponse(ret)


def get_lines_near_position(request, position_x, position_y, line_type_id):
    """Returns all line segments of a given type that are at least the type's minimum_distance
     from the given position.

     Format:
     {
        id: {
            line
            width
        }
     }
     """

    position_x = float(position_x)
    position_y = float(position_y)
    line_type_id = int(line_type_id)

    ret = {}

    if not LineType.objects.filter(id=line_type_id).exists():
        # This is an invalid request, the line type doesn't exist!
        logging.warn("Lines of non-existent LineType {} requested!".format(line_type_id))
        return ret

    line_type = LineType.objects.get(id=line_type_id)

    # Create a circle which the visible objects overlap with
    visibility_circle_center = geos.Point(position_x, position_y, srid=3857)
    visibility_circle_radius = line_type.display_radius

    visibility_circle = visibility_circle_center.buffer(visibility_circle_radius)

    # Retrieve all line segments from the database whose LineString intersects with the Circle
    #  and which have the given line_type
    segments = LineSegment.objects.filter(type=line_type_id, line__intersects=visibility_circle)

    # Add the segments to the response
    for segment in segments.all():
        # Ensure WebMercator coordinates
        line = segment.line
        line.transform(3857)

        ret[segment.id] = {
            "line": line.coords,
            "width": segment.width}

    return JsonResponse(ret)

