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


# construct the full path
def get_full_texture_path(local_path):
    return os.path.join(settings.STATICFILES_DIRS[0], local_path)


# replace the client prefix in debug mode
def replace_path_prefix(full_path):

    # do a null check, as it could happen to get an empty parameter
    if not full_path:
        return None

    if settings.DEBUG and hasattr(settings, "CLIENT_PATH_PREFIX"):
        server_prefix = settings.STATICFILES_DIRS[0]
        client_prefix = settings.CLIENT_PATH_PREFIX
        full_path = full_path.replace(server_prefix, client_prefix)

    # to provide relative paths to the client now we revert the
    # string join done in get_full_texture_path for now. There
    # is for sure a better overall implementation of this
    full_path = os.path.relpath(full_path, settings.STATICFILES_DIRS[0])

    # godot only accepts unix-style path separators ('/') so we replace them
    full_path = full_path.replace("\\", "/")

    return full_path
