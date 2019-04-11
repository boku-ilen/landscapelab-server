from django.contrib.gis.db import models

from assetpos.models import Asset


LAYER_TYPE = (
    (1, "K"),   # herb layer
    (2, "S2"),  # lower shrubs
    (3, "S1"),  # larger shrubs
    (4, "B2"),  # lower tree layer
    (5, "B1"),  # high/main tree layer
)

DISTRIBUTION_TYPE = (
    (1, "Random"),
    (2, "Clumping")
)


class Species(models.Model):

    # the binary name identifier (botanic name)
    genus_name = models.TextField()
    epithet_name = models.TextField()

    # the (optional) common name of the plant (TODO: translation?)
    common_name = models.TextField()

    # the maximum height of this type of plant in centimeters
    max_height = models.IntegerField()


# currently just a separator of different layers with approximately the same height of the associated plants
# TODO: What would be sensible max_heights for each layer? (required for size of mesh to draw on in client)
class VegetationLayer(models.Model):

    layer_type = models.PositiveIntegerField(choices=LAYER_TYPE, default=None)


# TODO: decide if we want to subclass Asset for that?
# TODO: or how do we connect an asset with a single instance (including custom height and maybe other parameters)
# TODO: alternatively we can provide a height range and the height is generated at runtime
# FIXME: alternative name SpeciesInstance (?) - I think SpeciesRepresentation is fine, as this is a general description
class SpeciesRepresentation(models.Model):

    # the species which is represented
    species = models.ForeignKey(Species, on_delete=models.PROTECT)

    # the associated 3d-asset (only shown up close?)
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, null=True)  # FIXME!

    # the billboard representation
    billboard = models.TextField()  # TODO: how to store?

    # the VegetationLayer this plant is in
    # TODO: Choose automatically based on avg_height and sigma_height or max_height in Species?
    vegetation_layer = models.PositiveIntegerField(choices=LAYER_TYPE, default=None)

    # how this plant is distributed
    distribution_type = models.PositiveIntegerField(choices=DISTRIBUTION_TYPE, default=1)
    distribution_density = models.FloatField(default=1)

    # TODO: maybe we want to abstract propability distribution functions in the future?
    # for now we assume a normal distributed height for all species
    # this value gives the average height in this occurrence in centimeters
    avg_height = models.IntegerField()
    # the sigma value (scattering for normal distribution)
    sigma_height = models.FloatField()

    # TODO: the species definition xml http://vterrain.org/Implementation/Formats/species.html
    # TODO: also defines shadow values to alter the plant's cast shadow
    # TODO: do we want to implement this?


# TODO: might be abstract as we have to differentiate between assets and shaders
class SpeciesOccurance(models.Model):
    pass


class Phytocoenosis(models.Model):
    """A specific plant community with multiple specific SpeciesRepresentations and their distribution.

    Includes a distribution graphic which defines how often plants occur and how they are distributed.
    Thus, behavior like 'single tree X is surrounded by many plants Y and few plants Z' can be accurately modeled

    Additional albedo and bumpmap textures can be provided. If possible, those are displayed instead of the orthophoto
    to increase detail.

    The optional texture at heightmap_detail_path is added to the heightmap in order to allow for smaller-scale detail.
    """

    name = models.TextField()

    speciesRepresentations = models.ManyToManyField(SpeciesRepresentation)

    # TODO: This is not actually used - should we save the path here, or just use a pathset string like it is now?
    distribution_graphic_path = models.TextField()

    albedo_path = models.TextField(null=True)
    normal_path = models.TextField(null=True)

    heightmap_detail_path = models.TextField(null=True)

    # TODO: we might want to add additional parameters to make the parametrisation
    # TODO: of the algorithm which chooses the Phytocoenosis more robust - currently
    # TODO: it needs to be selected manually or is completely random
    # e.g.
    # the height parameters of the appearance in meters
    min_height = models.IntegerField(null=True)
    max_height = models.IntegerField(null=True)
    # the slope parameters of the appearance as divisor of length to height
    min_slope = models.FloatField(null=True)
    max_slope = models.FloatField(null=True)
