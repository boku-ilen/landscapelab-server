import signal
import os
from landscapelab import utils


# this method is run at startup of the django stack
def startup(wsgi=False):

    # setup logging properly - make it possible to dynamically reload logging configuration
    utils.reload_logging(None)
    if not os.name == 'nt' and not wsgi:
        signal.signal(signal.SIGHUP, utils.reload_logging)
