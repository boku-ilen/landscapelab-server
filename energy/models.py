from django.contrib.gis.db import models

from assetpos.models import AssetPositions, AssetType
from location.models import Scenario


# this associates the energy location to an asset position to improve lookup performance
class AssetpositionToEnergylocation(models.Model):

    # the reference to the asset position
    asset_position = models.ForeignKey(AssetPositions, on_delete=models.SET_NULL, null=False)

    # the reference to the energy location
    energy_location = models.ForeignKey(AssetPositions, on_delete=models.SET_NULL, null=False)


#
class EnergyLocation(models.Model):

    # the surrounding polygon which indicates the same energy yield
    polygon = models.PolygonField()

    # the associated asset type
    asset_type = models.ForeignKey(AssetType, on_delete=models.SET_NULL, null=False)

    # the energy production which is yielded by placing one asset of the associated asset type
    energy_production = models.FloatField()


# the energy value which is the target for a specific asset type in a scenario (in mwh)
class EnergyTargets(models.Model):

    # the associated asset type
    asset_type = models.ForeignKey(AssetType, on_delete=models.SET_NULL, null=False)

    # the associated scenario
    scenario_id = models.ForeignKey(Scenario, on_delete=models.SET_NULL, null=False)

    # the target value in mwh
    target_value = models.FloatField(null=False, default=0)
