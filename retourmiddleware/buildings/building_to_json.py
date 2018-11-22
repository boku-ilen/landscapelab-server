import fiona
import logging
logger = logging.getLogger('MainLogger')


def get_buildings(modifiers):
    logger.info("generating building data")

    out = []

    with fiona.open(modifiers['filename']) as source:
        logger.debug(source)

        if 'bounds' in modifiers:
            # b = modifiers['bounds']
            # source.filter(bbox=(b['x_min'], b['y_min'], b['x_max'], b['y_max']))
            pass
        else:
            for f in source.filter():
                '''f['geometry'] = {
                    'type': 'Point',
                    'coordinates': f['geometry']['coordinates'][0][0]
                }'''
                out.append({
                    'id': f['id'],
                    'coordinates': f['geometry']['coordinates'],
                    'floors': 1
                })
                '''if len(f['geometry']['coordinates']) > 1:
                    logger.error(len(f['geometry']['coordinates']))
                '''
                # out.append(f)

    return {"Data": out}


def mean_coord(coordinates):
    x_mean = 0
    y_mean = 0
    count = 0

    for coord in coordinates:
        x_mean += coord[0]
        y_mean += coord[1]
        count += 1

    if count > 0:
        x_mean /= count
        y_mean /= count
    return [x_mean, y_mean]