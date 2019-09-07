from django.conf.urls import url

from . import views

urlpatterns = [

    # request the energy production of a certain location
    url(r'^location/(?P<asset_position_id>(\d+)).json$',
        views.get_json_energy_by_location, name='get_energy_by_location'),

    # Request energy contribution of an asset type
    url(r'^contribution/(?P<scenario_id>(\d+))/(?P<asset_type_id>(\d+)).json$',
        views.get_energy_contribution, name='get_energy_contribution_asset_type'),

    # Request energy contribution of all assets
    url(r'^contribution/(?P<scenario_id>(\d+))/all.json$',
        views.get_energy_contribution, name='get_energy_contribution_global')

]
