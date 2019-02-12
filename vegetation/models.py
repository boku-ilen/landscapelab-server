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

    # the associated 3d-asset (only shown up close?)
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
        (5, "K")
    )

    layer_type = models.PositiveIntegerField(choices=LAYER_TYPE, default=None)


class Phytocoenosis(models.Model):
    """A specific plant community with multiple specific SpeciesRepresentations and their distribution.

    Includes a distribution graphic which defines how often plants occur and how they are distributed.
    Thus, behavior like 'single tree X is surrounded by many plants Y and few plants Z' can be accurately modeled
    """

    name = models.TextField()

    speciesRepresentations = models.ManyToManyField(SpeciesRepresentation)

    # TODO: move to own class? probably not necessary, since these are very specific to the phytocoenosis and plant IDs
    distribution_graphic_path = models.TextField()  # or 'distribution_graphic = models.ImageField()'?

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

    # the client has separate modules for each layer so we can fine-tune at what point they're rendered at what detail
    # thus, the client requests a phytocoenosis + a specific layer in that phytocoenosis
    def for_layer(self, layer: VegetationLayer):
        """Get the distribution and the plants of the phytocoenosis for a specific VegetationLayer (in one image)"""

        # the client fills the shader of a specific vegetation layer with the distribution graphic and an image
        # containing all sprites. this means the for_layer function will return the distribution graphic of the
        # phytocoenosis, but with the pixels set to values which correspond to the plants in this specific layer. for
        # example: phytocoenosis has plants of id 2, 3, 5, 6, 7 and a distribution graphic. plants 3 and 5 are in the
        # requested layer S1. therefore, the server sends an image containing the sprites for plants 3 and 5 + the
        # distribution graphic with the pixels of value 3 set to 1, the pixels of value 5 set to 2, and all other
        # pixels set to 0, since nothing should be drawn at that layer on these positions. to make it possible for
        # the client to parse the spritesheet, the total number of sprites in the image is also sent.
        #
        # this is useful because we can render the layer with the biggest average height first, and with rising LOD,
        # render continuously smaller layers.
        #
        # this is assuming every species only has one sprite!
        # how could we pack an arbitrary number of sprites?...
        # idea: repeat everything and send number of repeats
        # e.g. if there are 2 available sprites for ID 1, and 3 for ID 2, the spritesheet would look like this:
        # (sprite for 1) (sprite for 2) (sprite for 1) (sprite for 2) (empty) (sprite for 2)
        # the client is sent the number of species in that sheet (2) and the number of repeats (3).
        # in a PNG, the empty pixels should not be a problem for file size.
