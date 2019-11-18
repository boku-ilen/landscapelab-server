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
    url(r'^start_session/(?P<scenario_id>[0-9]+)', views.start_session, name="start_session"),

    # adds a new location (a.k.a.: point of interest) to the server
    url(r'^create/(?P<name>(.*))/(?P<meter_x>[-+]?\d*\.\d+)/'
        r'(?P<meter_y>[-+]?\d*\.\d+)/(?P<scenario_id>(\d+))',
        views.register_location, name="register_location"),

    # removes an existing location from the server
    url(r'^remove/(?P<location_name>(.*))/(?P<scenario_id>(\d+))$',
        views.remove_location, name='remove_location'),

    # increases the order-field of a location by one
    url(r'^increase_order/(?P<location_name>(.*))$',
        views.increase_location_order, name='increase_location_order'),

    # decreases the order-field of a location by one
    url(r'^decrease_order/(?P<location_name>(.*))$',
        views.decrease_location_order, name='decrease_location_order')
]
