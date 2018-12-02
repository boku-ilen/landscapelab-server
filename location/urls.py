from django.conf.urls import url
from . import views


urlpatterns = [

    # get a list of all available projects (locations) and some necessairy parameters
    url(r'^project/list.json', views.project_list, name="project_list"),

    # a helper request which returns altitude and azimuth angles of the sun of a given date and time
    url(r'^sunposition/(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/(?P<hour>\d{2})/(?P<minute>\d{2})/'
        r'(?P<long>[-+]?\d*\.\d+)/(?P<lat>[-+]?\d*\.\d+)/(?P<elevation>\d*\.\d+).json',
        views.sunposition, name="sunposition"),

    # register an impression
    url(r'^impression/(?P<x>[-+]?\d*\.\d+)/(?P<y>[-+]?\d*\.\d+)/(?P<elevation>\d*\.\d+)/'
        r'(?P<target_x>[-+]?\d*\.\d+)/(?P<target_y>[-+]?\d*\.\d+)/(?P<target_elevation>\d*\.\d+)',
        views.register_impression, name="register_impression"),
]
