from django.conf.urls import url

from buildings import views
from buildings import import_buildings

urlpatterns = [
    # url(r'^get/', views.get_buildings, name="buildings"),
    #url(r'^', views.index, name="index"), # TODO DEPRECATED REMOVE AS SOON AS CLIENT NO LONGER RELIES ON THIS
    url(r'^get_from_bbox/(?P<x_min>(\d+(?:\.\d+)))/(?P<y_min>(\d+(?:\.\d+)))/(?P<x_max>(\d+(?:\.\d+)))/(?P<y_max>(\d+(?:\.\d+)))', views.get_from_bbox, name="buildings"),
    url(r'^scan/(?P<filename>[\w,\s-]+\.shp)/(?P<scenario_id>\d+)$', import_buildings.scan_buildings, name="scan"),
]