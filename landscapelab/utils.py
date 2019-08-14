import logging.config
import os
from itertools import tee
from django.conf import settings


# from https://stackoverflow.com/questions/5434891/iterate-a-list-as-pair-current-next-in-python
# returns the next value and the value thereafter of an iterator
from django.http import HttpResponse


delimiter = "/"


def get_static_file_dir():
    """Returns the STATICFILES_DIRS[0] from the Django settings, but always
     with the global delimiter"""

    return settings.STATICFILES_DIRS[0].replace("\\", delimiter)


def lookahead(iterable):
    """"s -> (s0,s1), (s1,s2), (s2, s3), ..."""
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def remove_heading_delimiter(path):
    """Removes the path delimiter from the start of the given path,
    if it is present.
    Note that this should not be done with absolute paths (on Linux)!"""

    if path.startswith(delimiter):
        path = path[len(delimiter):]

    return path


def remove_trailing_delimiter(path):
    """Removes the path delimiter from the end of the given path,
     if it is present"""

    if path.endswith(delimiter):
        path = path[:len(path)-len(delimiter)]

    return path


def join_path(*pieces):
    """"Joins a path like os.path.join, but always with our global delimiter
     instead of the system default"""

    return delimiter.join([remove_trailing_delimiter(piece) for piece in pieces])


# this dynamically reloads the logging configuration
def reload_logging(request):
    if not os.path.isfile(settings.LOGFILE):
        print("WARNING: {} does not exist - logging could not be initialized".format(settings.LOGFILE))
    else:
        logging.config.fileConfig(settings.LOGFILE)

    if request is not None:
        return HttpResponse(status=200)


def get_full_texture_path(local_path):
    """Turns a local resource path into a full path with our global delimiter"""

    return delimiter.join([get_static_file_dir(), local_path])


def replace_path_prefix(full_path):
    """Replaces the local server prefix of the path with the client prefix,
    if it is defined in the debug settings"""

    # do a null check, as it could happen to get an empty parameter
    if not full_path:
        return None

    # Remove the server part
    static_file_dir = remove_trailing_delimiter(get_static_file_dir())
    full_path = full_path.replace(static_file_dir, "")

    # Remove any heading or trailing delimiters of that new local path
    full_path = remove_trailing_delimiter(full_path)
    full_path = remove_heading_delimiter(full_path)

    # Add the client prefix if it is present
    if settings.DEBUG and hasattr(settings, "CLIENT_PATH_PREFIX"):
        client_prefix = settings.CLIENT_PATH_PREFIX
        full_path = join_path(client_prefix, full_path)

    # If there was a backslashed path somewhere, make sure to replace it with our delimiter
    full_path = full_path.replace("\\", delimiter)

    return full_path
