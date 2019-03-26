import logging.config
import os
from itertools import tee
from django.conf import settings


# from https://stackoverflow.com/questions/5434891/iterate-a-list-as-pair-current-next-in-python
# returns the next value and the value thereafter of an iterator
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

