from django.conf.urls import url

from buildings import views

urlpatterns = [

    # this is for testing only
    url(r'^get_from_bbox/(?P<x_min>(\d+(?:\.\d+)))/(?P<y_min>(\d+(?:\.\d+)))/(?P<x_max>(\d+(?:\.\d+)))/'
        r'(?P<y_max>(\d+(?:\.\d+)))', views.get_from_bbox, name="buildings"),

]
