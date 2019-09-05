from django.conf.urls import url

from . import views

urlpatterns = [

    # get the attributes of an asset
    url(r'^attributes/(?P<asset_id>(\d+)).json$', views.get_attributes, name='get_attributes'),

    # Creates a new instance of an asset (assets defined in fixture)
    url(r'^create/(?P<asset_id>(\d+))/(?P<meter_x>[-+]?\d*\.\d+)/(?P<meter_y>[-+]?\d*\.\d+)$',
        views.register_assetposition, name='register_assetposition'),

    # Creates a new instance of an asset with a non-zero orientation (assets defined in fixture)
    url(r'^create/(?P<asset_id>(\d+))/(?P<meter_x>[-+]?\d*\.\d+)/(?P<meter_y>[-+]?\d*\.\d+)/(?P<orientation>(\d+))$',
        views.register_assetposition, name='register_assetposition'),

    # Deletes an asset instance
    url(r'^remove/(?P<assetpos_id>(\d+))$',
        views.remove_assetposition, name='remove_assetposition'),

    # Get the position for one asset instance
    url(r'^get/(?P<assetpos_id>(\d+))$',
        views.get_assetposition, name='get_assetposition'),

    # Set the position of an asset instance to the given x, y projected meters
    url(r'^set/(?P<assetpos_id>(\d+))/(?P<meter_x>[-+]?\d*\.\d+)/(?P<meter_y>[-+]?\d*\.\d+)$',
        views.set_assetposition, name='set_assetposition'),

    # Request all locations of a specific asset globally
    url(r'^get_all/(?P<asset_id>(\d+)).json$',
        views.get_assetpositions_global, name='get_assetpositions_global'),

    # Request all locations of an assettype and a given tile
    url(r'^get_all/(?P<assettype_id>(\d+))/(?P<tile_x>(\d+(?:\.\d+)))/(?P<tile_y>(\d+(?:\.\d+)))/(?P<zoom>(\d+)).json$',
        views.get_assetpositions, name='get_assetpositions'),

    # Request all AssetPositions of an AssetType close to a given point (using the AssetType's display_radius)
    url(r'^get_near/by_asset/(?P<asset_or_assettype_id>(\d+))/'
        r'(?P<meter_x>(\d+(?:\.\d+)))/(?P<meter_y>(\d+(?:\.\d+))).json$',
        views.get_near_assetpositions, name='get_near_assetpositions'),

    # Request all AssetPositions of an AssetType close to a given point (using the AssetType's display_radius)
    url(r'^get_near/by_assettype/(?P<asset_or_assettype_id>(\d+))/'
        r'(?P<meter_x>(\d+(?:\.\d+)))/(?P<meter_y>(\d+(?:\.\d+))).json$',
        views.get_near_assetpositions, {"by_assettype": True}, name='get_near_assetpositions'),

    # returns a nested json of all (editable / nonabstract) assettypes
    url(r'^get_all_assettypes.json', views.getall_assettypes, {"include_abstract": True}, name="get_all_assettypes"),
    url(r'^get_all_editable_assettypes.json', views.getall_assettypes, {"editable": True}, name="get_all_editable"),
    url(r'^get_all_nonabstract_assettypes.json', views.getall_assettypes, name="get_all_editable"),
]
