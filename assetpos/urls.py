# from django.urls import path
from django.conf.urls import url

from . import views

urlpatterns = [
    # path('',views.index, name='index'),
    url(r'^', views.index, name="index"),

    # request the locations of an assettype and a given tile
    url(r'^get/(?P<assettype_id>\s)/(?P<tile_x>(\d+))/(?P<tile_y>(\d+))/(?P<zoom>(\d+)).json$',
        views.get_assetposition, 'get_assetposition'),

]
