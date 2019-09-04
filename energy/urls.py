from django.conf.urls import url

from . import views

# request the energy production of an asset
url(r'^energy_contribution/(?P<asset_id>(\d+))/asset.json$',
    views.get_energy_contribution, name='get_energy_contribution_asset'),

# Request energy contribution of an asset type
url(r'^energy_contribution/(?P<asset_type_id>(\d+)).json$',
    views.get_energy_contribution, name='get_energy_contribution_asset_type'),

# Request energy contribution of all assets
url(r'^energy_contribution/all.json$',
    views.get_energy_contribution, name='get_energy_contribution_global'),

