import numpy as np


def calcAssetPos(dataset, path):
    path_parts = path.split('/')

    layer = dataset.GetLayer()

    d = {'Data': []}
    # for feature in layer:
    #     geom = feature.GetGeometryRef()
    #     d['Data'] = vert_to_asset(geom, d['Data'])

    dist = 100
    if len(path_parts) == 4:
        dist = int(path_parts[3])
    for feature in layer:
        geom = feature.GetGeometryRef()
        d['Data'] = asset_on_lines(geom, dist, d['Data'])

    return d


# places one asset on each vertex... will have to make a more advanced method later
def vert_to_asset(geom, d=[]):
    if geom.GetPointCount() > 0:
        for i in range(0, geom.GetPointCount()):
            pt = geom.GetPoint(i)
            d.append([d.__len__(), pt[0], pt[1]])

    if geom.GetGeometryCount() > 0:
        for i in range(0, geom.GetGeometryCount()):
            d = vert_to_asset(geom.GetGeometryRef(i), d)

    return d


# this function places assets on the edges of the polygon in regular intervals (dist)
# at the moment the covered distance is reset at each vertex, will have to make some changes later
def asset_on_lines(geom, dist, d=[]):
    if geom.GetPointCount() > 0:
        lp = geom.GetPoint(0)
        lp = np.array([lp[0], lp[1]])
        for i in range(1, geom.GetPointCount()):
            pt = geom.GetPoint(i)
            pt = np.array([pt[0], pt[1]])
            dis = np.linalg.norm(pt - lp)

            while dis > 0:
                dis -= dist
                if dis > 0:
                    ap = pt + normalize(lp - pt) * dis
                    d.append([d.__len__(), ap[0], ap[1]])

            lp = pt

    if geom.GetGeometryCount() > 0:
        for i in range(0, geom.GetGeometryCount()):
            d = asset_on_lines(geom.GetGeometryRef(i), dist, d)

    return d


def normalize(v):
    return v / np.linalg.norm(v)
