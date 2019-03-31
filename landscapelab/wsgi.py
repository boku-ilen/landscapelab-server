"""
WSGI configuraton for the landscapelab-server

It exposes the WSGI callable as a module-level variable named ``application``.
"""

import os
import sys
import landscapelab.startup as startup

from django.core.wsgi import get_wsgi_application

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "landscapelab.settings")

# run startup scripts
startup.startup(wsgi=True)

application = get_wsgi_application()
