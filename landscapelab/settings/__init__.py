from django.conf import settings
from split_settings.tools import optional, include
import logging
import os

logger = logging.getLogger(__name__)
LOCAL_SETTINGS = "local_settings.py"

# setup the django settings
include(
    'default_settings.py',
    optional(LOCAL_SETTINGS)
)

# give a warning if the optional local settings are not found
if not os.path.isfile(os.path.join(settings.BASE_DIR, LOCAL_SETTINGS)):
    logger.warning("could not find local settings file in {}"
                   " - are you sure your setup is correct?".format(LOCAL_SETTINGS))
