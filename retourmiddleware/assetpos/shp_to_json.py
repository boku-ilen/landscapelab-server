import random
import logging

from matplotlib.tri import Triangulation

from .util import *

logger = logging.getLogger('MainLogger')

# returns a dictionary with tree data (model and coordinates)
def get_trees(data, modifiers):
    tree_multiplier = modifiers['tree_multiplier']
    place_border = modifiers['place_border']
    place_area = modifiers['place_area']
    area_percentage = modifiers['area_percentage']

    models = get_models()

    layer = data.GetLayer()

    tree_info = []

    for feature in layer:
        points = []
        points = put_trees(
            feature.GetGeometryRef(),
            int(feature.GetFieldAsInteger(feature.GetFieldIndex("trees")) * tree_multiplier),
            place_border,
            place_area,
            area_percentage,
            points
        )

        for point in points:
            p = point.tolist()
            tree_info.append({
                'model': random.choice(models),
                'coord': p  # [int(p[0]), int(p[1])]
            })

    logger.info("finished with %d trees" % len(tree_info))
    return {'Data': tree_info}


# returns the models to select from
# just a dummy at the moment
def get_models():
    return ['fichte1',
            'fichte2',
            'fichte3',
            'eiche1',
            'eiche2',
            'buche',
            'tanne1',
            'tanne2',
            'kiefer'
            ]


# recursively goes through geometry (since they can be nested) and returns the points where trees should be placed
def put_trees(geom, tree_count, place_border, place_area, area_percentage, points=[]):
    if geom.GetPointCount() > 0:
        if place_border:
            points = set_border_trees(tree_count * (1 - area_percentage), geom, points)
        if place_area:
            # points = set_area_trees(tree_count / 2, geom, points) not implemented yet
            points = set_area_trees(tree_count * area_percentage, geom, points)
        return points

    if geom.GetGeometryCount() > 0:
        for i in range(0, geom.GetGeometryCount()):
            points = put_trees(
                geom.GetGeometryRef(i),
                tree_count / geom.GetGeometryCount(),
                place_border,
                place_area,
                area_percentage,
                points
            )
    return points


# sets points alongside the border of a given polygon
def set_border_trees(tree_count, geom, points):
    perimeter = get_polygon_perimeter(geom)

    if tree_count > 0:
        dist = perimeter / tree_count

        lp = cut_vector(geom.GetPoint(0))
        remaining_distance = 0
        for p_id in range(1, geom.GetPointCount()):
            ap = cut_vector(geom.GetPoint(p_id))

            remaining_distance += length(ap - lp)
            while remaining_distance > 0:
                points.append(lp + ((ap - lp) / length(ap - lp)) * remaining_distance)
                remaining_distance -= dist
            lp = ap

    return points


def set_area_trees(tree_count, geom, points):
    triangles = triangulate_polygon(geom)
    triangle_probability = calculate_triangle_area(triangles)
    geometry_area = sum(triangle_probability)
    for n in range(len(triangle_probability)):
        triangle_probability[n] /= geometry_area

    while tree_count > 0:
        r = random.random()
        selected_triangle = -1
        while r > 0 and selected_triangle < len(triangles)-1:
            selected_triangle += 1
            r -= triangle_probability[selected_triangle]
        points.append(random_point_on_triangle(triangles[selected_triangle]))
        tree_count -= 1

    return points


# returns the perimeter of a given polygon
def get_polygon_perimeter(geom):
    dist = 0
    if geom.GetPointCount() > 0:
        lp = cut_vector(geom.GetPoint(0))
        for n in range(1, geom.GetPointCount()):
            ap = cut_vector(geom.GetPoint(n))
            dist += length(lp - ap)
            lp = ap
    return dist


def triangulate_polygon(geom):
    vertices = []
    for i in range(geom.GetPointCount()):
        vertices.append(cut_vector(geom.GetPoint(i)))

    xp = []
    yp = []
    for v in vertices:
        xp.append(v[0])
        yp.append(v[1])
    tris = Triangulation(xp, yp).triangles
    triangles = []
    for t in tris:
        triangles.append([vertices[t[0]], vertices[t[1]], vertices[t[2]]])
    return triangles


# calculates the area of each triangle in a given triangle array and returns the results in an array
def calculate_triangle_area(triangles):
    area = []
    for t in triangles:
        a = length(t[0] - t[1])
        b = length(t[1] - t[2])
        c = length(t[2] - t[0])
        s = (a + b + c) / 2
        area.append((s * (s - a) * (s - b) * (s - c)) ** 0.5)
    return area


# calculates a random point within a given triangle and returns it
# according to http://mathworld.wolfram.com/TrianglePointPicking.html this method should space the points evenly
# not sure if that is correct or if my implementation of the solution still spaces them correctly
def random_point_on_triangle(t):
    v1 = t[1] - t[0]
    v2 = t[2] - t[0]

    while True:
        r1 = random.random()
        r2 = random.random()
        if r1 + r2 < 1.0:
            p = v1 * r1 + v2 * r2
            p += t[0]
            return p


# other solution to set area trees
# was not completed and would probably be way less sufficient than the current solution
#
#
# # sets trees inside a polygon
# # depends on get_polygon_bounding_box and in_polygon which are not implemented yet
# # could also be optimized a lot since it more or less relies on brute-force
# def set_area_trees(tree_count, geom, points):
#     bbox = get_polygon_bounding_box(geom)
#
#     while tree_count > 0:
#         pt = np.array([random.random(bbox[0], bbox[2]), random.random(bbox[1], bbox[3])])
#         if in_polygon(pt, geom):
#             points.append(pt)
#             tree_count -= 1
#
#     return points
#
#
# # returns the bounding box of a given polygon
# # not implemented yet
# # [x-min, y-min, x-max, y-max]
# def get_polygon_bounding_box(geom):
#     return [-10, -10, 10, 10]
#
#
# # returns true if a given point is inside a given polygon
# # not implemented yet
# def in_polygon(pt, geom):
#     return True
