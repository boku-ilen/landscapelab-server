from django.conf.urls import url
from location import views


urlpatterns = [

    # get a list of all available scenarios and some necessary parameters
    url(r'^scenario/list.json', views.scenario_list, name="scenario_list"),

    # get a list of all available services for a given scenario
    url(r'^services/(?P<scenario_id>\d*).json', views.services_list, name="services_list"),

    # get the associated information of a printed map
    url(r'^map/(?P<map_id>\d*).json', views.get_map, name="get_map"),

    # a helper request which returns altitude and azimuth angles of the sun of a given date and time
    url(r'^sunposition/(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/(?P<hour>\d{2})/(?P<minute>\d{2})/'
        r'(?P<long>[-+]?\d*\.\d+)/(?P<lat>[-+]?\d*\.\d+)/(?P<elevation>\d*\.\d+).json',
        views.sunposition, name="sunposition"),

    # register an impression
    url(r'^impression/(?P<x>[-+]?\d*\.\d+)/(?P<y>[-+]?\d*\.\d+)/(?P<elevation>\d*\.\d+)/'
        r'(?P<target_x>[-+]?\d*\.\d+)/(?P<target_y>[-+]?\d*\.\d+)/(?P<target_elevation>\d*\.\d+)/'
        r'(?P<session_id>[0-9]+)',
        views.register_impression, name="register_impression"),

    # starts a new session and returns the session key
    url(r'^start_session/(?P<scenario_id>[0-9]+)', views.start_session, name="start_session")

]
