from django.http import HttpResponse
from django.contrib.staticfiles import finders

import os.path
import logging
import json

logger = logging.getLogger('MainLogger')


# delivers given raster as json
def request_to_png_response(filename):

    img_name = finders.find(os.path.join('maps', filename))

    # Open the data source and read in the extent
    try:
        BASE = os.path.dirname(os.path.abspath(__file__))
        img = open(os.path.join(BASE, img_name), "rb")
    except RuntimeError as e:
        logger.error('Unable to open %s' % img_name)
        logger.error(e)
        return {"Error": "failed to open file"}
    except TypeError as e:
        logger.error('Unable to open %s' % img_name)
        logger.error(e)
        return {"Error": "failed to open file"}

    img_data = img.read()
    img_dict = {}

    # The image bytes will be sent as JSON, so we need to create a dictionary out of the image bytes.
    # This is probably somewhat redundant and inefficient, but it works!
    for i in range(len(img_data)):
        img_dict[i] = int(img_data[i])

    return img_dict
