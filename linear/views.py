from django.contrib.gis import geos

from linear.models import LineType, LineSegment
import logging


def get_lines_near_position(position_x, position_y, line_type_id):
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

    ret = {}

    if not LineType.objects.filter(id=line_type_id).exists():
        # This is an invalid request, the line type doesn't exist!
        logging.warn("Lines of non-existent LineType {} requested!".format(line_type_id))
        return ret

    line_type = LineType.objects.get(id=line_type_id)

    # Create a circle which the visible objects overlap with
    visibility_circle_center = geos.Point(position_x, position_y)
    visibility_circle_radius = line_type.display_radius

    visibility_circle = visibility_circle_center.buffer(visibility_circle_radius)

    # Retrieve all line segments from the database whose LineString intersects with the Circle
    #  and which have the given line_type
    segments = LineSegment.objects.filter(type=line_type_id, line__intersects=visibility_circle)

    # Add the segments to the response
    for segment in segments.all():
        ret[segment.id] = {
            "line": segment.line,
            "width": segment.width}

    return ret

