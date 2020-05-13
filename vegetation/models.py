from django.contrib.gis.db import models

from assetpos.models import Asset

LAYER_TYPE = (
    (1, "K"),   # herb layer
    (2, "S2"),  # lower shrubs
    (3, "S1"),  # larger shrubs
    (4, "B2"),  # lower tree layer
    (5, "B1")  # high/main tree layer
)

LAYER_MAXHEIGHTS = (
    (1, 1.0),
    (2, 2.5),
    (3, 7.0),
    (4, 12.0),
    (5, 30.0)
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


class SpeciesRepresentation(models.Model):
    # the species which is represented
    # FIXME: This is currently nullable since our dataset does not have species, and they're not technically required.
    #  in production, that shouldn't be the case.
    species = models.ForeignKey(Species, on_delete=models.PROTECT, null=True)

    # the associated 3d-asset (only shown up close?)
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, null=True)  # FIXME!

    # path to the billboard representation
    billboard = models.TextField()

    # the VegetationLayer this plant is in
    # TODO: Choose automatically based on avg_height and sigma_height or max_height in Species? (Currently done in
    #  vegetation_csv_to_fixture command)
    vegetation_layer = models.PositiveIntegerField(choices=LAYER_TYPE, default=None)

    # how this plant is distributed
    distribution_type = models.PositiveIntegerField(choices=DISTRIBUTION_TYPE, default=1)

    # density in occurances per m²
    distribution_density = models.FloatField(default=1)

    # for now we assume a normal distributed height for all species
    # this value gives the average height in this occurrence in centimeters
    avg_height = models.FloatField()

    # the sigma value (scattering for normal distribution)
    sigma_height = models.FloatField()

    # TODO: the species definition xml http://vterrain.org/Implementation/Formats/species.html
    # TODO: also defines shadow values to alter the plant's cast shadow
    # TODO: do we want to implement this?


# TODO: SpeciesRepresentations which are in a Phytocoenosis are rendered via a shader. This
#  class is for instances of plants at specific representations.
#  This is actually just a specific type of Asset! (subclass Asset?)
class SpeciesOccurance(models.Model):
    pass


class Phytocoenosis(models.Model):
    """A specific plant community with multiple specific SpeciesRepresentations and their distribution.

    Includes a distribution graphic which defines how often plants occur and how they are distributed.
    Thus, behavior like 'single tree X is surrounded by many plants Y and few plants Z' can be accurately modeled

    Additional albedo, normal and displacement textures can be provided. If possible, those are displayed instead of the
    orthophoto to increase detail.
    """

    name = models.TextField()

    speciesRepresentations = models.ManyToManyField(SpeciesRepresentation)

    albedo_path = models.TextField(null=True)
    normal_path = models.TextField(null=True)
    displacement_path = models.TextField(null=True)
