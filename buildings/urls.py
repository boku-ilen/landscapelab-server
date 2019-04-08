from django.conf.urls import url

from buildings import views
from buildings import import_buildings


urlpatterns = [

    # this is for testing only
    url(r'^get_from_bbox/(?P<x_min>(\d+(?:\.\d+)))/(?P<y_min>(\d+(?:\.\d+)))/(?P<x_max>(\d+(?:\.\d+)))/'
        r'(?P<y_max>(\d+(?:\.\d+)))', views.get_from_bbox, name="buildings"),

    # FIXME: this should be implemented via management/commands
    url(r'^scan/(?P<filename>[\w,\s-]+\.shp)/(?P<scenario_id>\d+)$', import_buildings.scan_buildings, name="scan"),

]