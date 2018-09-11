import random
import numpy as np


# returns a dictionary with tree data (model and coordinates)
def get_trees(data, request):
    models = get_models()

    layer = data.GetLayer()

    tree_info = []

    for feature in layer:
        points = []
        points = put_trees(
            feature.GetGeometryRef(),
            feature.GetFieldAsInteger(feature.GetFieldIndex("trees")),
            points
        )

        for point in points:
            p = point.tolist()
            tree_info.append({
                'model': random.choice(models),
                'coord': p  # [int(p[0]), int(p[1])]
            })

    print("finished with %d trees" % len(tree_info))
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
def put_trees(geom, tree_count, points=[]):
    if geom.GetPointCount() > 0:
        points = set_border_trees(tree_count / 2, geom, points)
        # points = set_area_trees(tree_count / 2, geom, points) not implemented yet
        return points

    if geom.GetGeometryCount() > 0:
        for i in range(0, geom.GetGeometryCount()):
            points = put_trees(
                geom.GetGeometryRef(i),
                tree_count / geom.GetGeometryCount(),
                points
            )
    return points


# sets points alongside the boarder of a given polygon
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


# sets trees inside a polygon
# depends on get_polygon_bounding_box and in_polygon which are not implemented yet
# could also be optimized a lot since it more or less relies on brute-force
def set_area_trees(tree_count, geom, points):
    bbox = get_polygon_bounding_box(geom)

    while tree_count > 0:
        pt = np.array([random.random(bbox[0], bbox[2]), random.random(bbox[1], bbox[3])])
        if in_polygon(pt, geom):
            points.append(pt)
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


# returns the bounding box of a given polygon
# not implemented yet
# [x-min, y-min, x-max, y-max]
def get_polygon_bounding_box(geom):
    return [-10, -10, 10, 10]


# returns true if a given point is inside a given polygon
# not implemented yet
def in_polygon(pt, geom):
    return True


# cuts off the third coordinate and turns into numpy array
def cut_vector(v):
    return np.array([v[0], v[1]])


# returns the length of a given vector
def length(v):
    return np.linalg.norm(v)
