import logging.config
import os
from itertools import tee
from django.conf import settings


# from https://stackoverflow.com/questions/5434891/iterate-a-list-as-pair-current-next-in-python
# returns the next value and the value thereafter of an iterator
from django.http import HttpResponse


def lookahead(iterable):
    """"s -> (s0,s1), (s1,s2), (s2, s3), ..."""
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


# this dynamically reloads the logging configuration
def reload_logging(request):
    if not os.path.isfile(settings.LOGFILE):
        print("WARNING: {} does not exist - logging could not be initialized".format(settings.LOGFILE))
    else:
        logging.config.fileConfig(settings.LOGFILE)

    if request is not None:
        return HttpResponse(status=200)


# construct the full path and replace the path prefix for remote test server setup in debug mode
def get_full_texture_path(local_path):
    full_path = os.path.join(settings.STATICFILES_DIRS[0], local_path)

    if settings.DEBUG and hasattr(settings, "CLIENT_PATH_PREFIX"):
        server_prefix = settings.STATICFILES_DIRS[0]
        client_prefix = settings.CLIENT_PATH_PREFIX
        full_path = full_path.replace(server_prefix, client_prefix)
    return full_path
