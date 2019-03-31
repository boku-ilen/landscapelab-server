# from django.urls import path
from django.conf.urls import url

from . import views

urlpatterns = [
    # path('',views.index, name='index'),
    # url(r'^', views.index, name="index"),

    # request the locations of an assettype and a given tile
    url(r'^get/(?P<assettype_id>(\d+))/(?P<tile_x>(\d+))/(?P<tile_y>(\d+))/(?P<zoom>(\d+)).json$',
        views.get_assetposition, name='get_assetposition'),

    # sets the position of an asset to the given x,y projected meters
    # TODO: draft - this is move only, how to register and create a new object (from lego)
    url(r'^set/(?P<asset_id>(\d+))/(?P<meter_x>[-+]?\d*\.\d+)/(?P<meter_y>[-+]?\d*\.\d+).coords$',
        views.set_assetposition, name=''),

]
