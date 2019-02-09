from django.contrib.gis.db import models

from assetpos.models import Asset


class Species(models.Model):

    # the binary name identifier (botanic name)
    genus_name = models.TextField()
    epithet_name = models.TextField()

    # the (optional) common name of the plant (TODO: translation?)
    common_name = models.TextField()

    # the maximum height of this type of plant in centimeters
    max_height = models.IntegerField()


# TODO: decide if we want to subclass Asset for that?
# TODO: or how do we connect an asset with a single instance (including custom height and maybe other parameters)
# TODO: alternatively we can provide a height range and the height is generated at runtime
# FIXME: alternative name SpeciesInstance (?)
class SpeciesRepresentation(models.Model):

    # the species which is represented
    species = models.ForeignKey(Species, on_delete=models.PROTECT)

    # the associated 3d-asset
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT)  # FIXME!

    # TODO: maybe we want to abstract propability distribution functions in the future?
    # for now we assume a normal distributed height for all species
    # this value gives the average height in this occurrence in centimeters
    avg_height = models.IntegerField()
    # the sigma value (scattering for normal distribution)
    sigma_height = models.FloatField()

    # the billboard representation
    billboard = models.TextField()  # TODO: how to store?

    # TODO: the species definition xml http://vterrain.org/Implementation/Formats/species.html
    # TODO: also defines shadow values to alter the plant's cast shadow
    # TODO: do we want to implement this?


# TODO: might be abstract as we have to differentiate between assets and shaders
class SpeciesOccurance(models.Model):
    pass


# currently just a separator of different layers with approximately the same
# height of the associated plants
class VegetationLayer(models.Model):
    LAYER_TYPE = (
        (1, "B1"),
        (2, "B2"),
        (3, "S1"),
        (4, "S2"),
        (5, "K")  # herb layer, which is rendered via a shader
    )

    layer_type = models.PositiveIntegerField(choices=LAYER_TYPE, default=None)


# this is a specific plant community as a set of appearance of different
# plants in different sizes and densities
class Phytocoenosis(models.Model):

    name = models.TextField()

    # TODO: we might want to add additional parameters to make the parametrisation
    # TODO: of the algorithm which chooses the Phytocoenosis more robust - currently
    # TODO: it needs to be selected manually or is completely random
    # e.g.
    # the height parameters of the appearance in meters
    min_height = models.IntegerField()
    max_height = models.IntegerField()
    # the slope parameters of the appearance as divisor of length to height
    min_slope = models.FloatField()
    max_slope = models.FloatField()
