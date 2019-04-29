from django.conf.urls import url

from . import views

urlpatterns = [

    # get the attributes of an asset
    url(r'^attributes/(?P<asset_id>(\d+)).json$', views.get_attributes, name='get_attributes'),

    # Creates a new asset (if possible)
    # FIXME: how to create the actual asset?
    url(r'^create/(?P<asset_id>(\d+))/(?P<meter_x>[-+]?\d*\.\d+)/(?P<meter_y>[-+]?\d*\.\d+)$',
        views.register_assetposition, name='register_assetposition'),

    # Deletes an asset
    url(r'^remove/(?P<assetpos_id>(\d+))$',
        views.remove_assetposition, name='remove_assetposition'),

    # Get the position for one asset
    url(r'^get/(?P<assetpos_id>(\d+))$',
        views.get_assetposition, name='get_assetposition'),

    # Set the position of an asset to the given x, y projected meters
    url(r'^set/(?P<assetpos_id>(\d+))/(?P<meter_x>[-+]?\d*\.\d+)/(?P<meter_y>[-+]?\d*\.\d+)$',
        views.set_assetposition, name='set_assetposition'),

    # Request all locations of an assettype and a given tile
    url(r'^get_all/(?P<assettype_id>(\d+))/(?P<tile_x>(\d+))/(?P<tile_y>(\d+))/(?P<zoom>(\d+)).json$',
        views.get_assetpositions, name='get_assetpositions'),

]
