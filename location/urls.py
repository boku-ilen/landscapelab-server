from django.conf.urls import url
from . import views


urlpatterns = [

    # get a list of all available projects (locations) and some necessairy parameters
    url(r'^project/list.json', views.project_list, name="project_list"),

    # get a list of all available services for a given scenario
    # TODO: change the API to include the scenario id in the request
    url(r'^areas', views.services_list, name="services_list"),

    # a helper request which returns altitude and azimuth angles of the sun of a given date and time
    url(r'^sunposition/(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/(?P<hour>\d{2})/(?P<minute>\d{2})/'
        r'(?P<long>[-+]?\d*\.\d+)/(?P<lat>[-+]?\d*\.\d+)/(?P<elevation>\d*\.\d+).json',
        views.sunposition, name="sunposition"),

    # register an impression
    url(r'^impression/(?P<x>[-+]?\d*\.\d+)/(?P<y>[-+]?\d*\.\d+)/(?P<elevation>\d*\.\d+)/'
        r'(?P<target_x>[-+]?\d*\.\d+)/(?P<target_y>[-+]?\d*\.\d+)/(?P<target_elevation>\d*\.\d+)/'
        r'(?P<session_id>[0-9]+)',
        views.register_impression, name="register_impression"),

    # create a session
    url(r'^session/(?P<area>[A-z0-9]+)', views.create_session, name="create_session")
]
