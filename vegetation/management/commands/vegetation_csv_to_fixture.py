import os
from ast import literal_eval

from django.core.management import BaseCommand

from landscapelab import utils
from vegetation.models import LAYER_MAXHEIGHTS

import logging
import csv
import json

logger = logging.getLogger(__name__)


AVG_HEIGHT_DEFAULT = 5.0
SIGMA_HEIGHT_DEFAULT = 1.0
SPECIES_DEFAULT = 0
DEFAULT_DISTRIBUTION_DENSITY = 1

BILLBOARD_PREFIX = "plant-sprites"
TEXTURE_PREFIX = "plant-textures"
ALBEDO_TEXTURE_NAME = "albedo.jpg"
NORMAL_TEXTURE_NAME = "normal.jpg"


class Command(BaseCommand):
    help = """
    Parses a vegetation CSV like https://docs.google.com/spreadsheets/d/1_IMhtppINbx7g0BfnqGm1nDEcCtxqW5wN6LY1EMx2-4
    to a JSON fixture that can be imported into the server's database.
    """

    def add_arguments(self, parser):
        parser.add_argument("--species_representations", type=str)
        parser.add_argument("--phytocoenosis", type=str)
        parser.add_argument("--outfile", type=str)

    def handle(self, *args, **options):
        # Input validation
        if "species_representations" not in options:
            logger.error("No species representations csv filename given!")
            return

        if "phytocoenosis" not in options:
            logger.error("No phytocoenosis csv filename given!")
            return

        if "outfile" not in options:
            logger.error("No output filename given!")
            return

        if not os.path.isfile(options["species_representations"]):
            logger.error("Invalid species representations file!")
            return

        if not os.path.isfile(options["phytocoenosis"]):
            logger.error("Invalid phytocoenosis file!")
            return

        jsonfile = open(options["outfile"], "w+")

        species_representation_data = get_csv_as_json(open(options["species_representations"], "r"),
                                                      "SpeciesRepresentation")
        phytocoenosis_data = get_csv_as_json(open(options["phytocoenosis"], "r"), "Phytocoenosis")

        parse_species_representation_data(species_representation_data)
        parse_phytocoenosis_data(phytocoenosis_data)

        json_data = species_representation_data + phytocoenosis_data

        jsonfile.write(json.dumps(json_data, sort_keys=False, indent=4, separators=(",", ": "), ensure_ascii=False))


def get_csv_as_json(csvfile, modelname):
    """Parses a CSV file and returns the data in the Django fixture format.
    The given modelname must match the name of the Django model this data corresponds to.
    """

    json_data = []

    reader = csv.DictReader(csvfile)

    for row in reader:
        json_data.append({"model": "vegetation.{}".format(modelname), "fields": row})

    return json_data


def parse_species_representation_data(json_data):
    """Parses a fixture list to the correct data types for species representations.
    The fields are parsed as follows:

    "id": int,
    "species": int,
    "avg_height": float,
    "sigma_height": float,
    "vegetation_layer": int,
    "distribution_density": float
    "billboard": string
    """

    to_be_deleted = []

    for index, raw_entry in enumerate(json_data):
        entry = raw_entry["fields"]

        try:
            # Check if the billboard field is set - the species representation is useless otherwise
            if not entry["billboard"]:
                logger.warn("Field with empty billboard at ID {} will not be included!".format(entry["id"]))
                to_be_deleted.append(index)  # Can't delete from list while iterating!
                continue

            entry["id"] = int(entry["id"])
            entry["species"] = int(entry["species"]) if entry["species"] else None
            entry["avg_height"] = float(entry["avg_height"] or AVG_HEIGHT_DEFAULT)
            entry["sigma_height"] = float(entry["sigma_height"] or SIGMA_HEIGHT_DEFAULT)
            entry["billboard"] = utils.join_path(BILLBOARD_PREFIX, entry["billboard"])

            # Get the layer based on the avg_height
            layer_set = False

            for (layer, max_height) in LAYER_MAXHEIGHTS:
                # TODO: The sigma_height should be added to this calculation in the future.
                #  For now, this works since we don't use the sigma_height here.
                if entry["avg_height"] <= max_height:
                    entry["vegetation_layer"] = layer
                    layer_set = True
                    break

            # If there was no fitting layer, set it to max, but issue a warning
            if not layer_set:
                entry["vegetation_layer"] = len(LAYER_MAXHEIGHTS)
                logger.warning("The plant with id {} is too high ({}) - the maximum layer has been assigned".format(
                    entry["id"], entry["avg_height"]))

            # Parse the distribution density, convert if needed (it's formatted like '10/ar')
            distribution_density_and_unit = entry["distribution_density"].split("/", 1)

            # Set to default value first in case of invalid or empty entry
            entry["distribution_density"] = DEFAULT_DISTRIBUTION_DENSITY

            # TODO: Should we keep those conversions, or will we not have entries of this format anymore?
            if len(distribution_density_and_unit) > 1:
                if distribution_density_and_unit[1] == "m²":
                    entry["distribution_density"] = float(distribution_density_and_unit[0])
                elif distribution_density_and_unit[1] == "ar":
                    entry["distribution_density"] = float(distribution_density_and_unit[0]) / 100
                elif distribution_density_and_unit[1] == "ha":
                    entry["distribution_density"] = float(distribution_density_and_unit[0]) / 10000

            logger.debug("Parsed vegetation with ID {}".format(entry["id"]))
        except ValueError:
            logger.error("One of the types in the json row {} did not have the correct type!"
                         " Please check the specification.".format(entry))

    # Delete the items which were flagged as invalid
    # We reverse to_be_deleted since otherwise, indices in json_data change while deleting!
    for index in reversed(to_be_deleted):
        del json_data[index]


def parse_phytocoenosis_data(json_data):
    """Parses a fixture list to the correct data types for phytocoenosis.
    The fields are parsed as follows:

    "id": int,
    "speciesRepresentations": list,
    "name": string,
    "albedo_path": string,
    "normal_path": string

    albedo_path and normal_path are built from the "texture" field.
    """

    for entry in json_data:
        entry = entry["fields"]

        try:
            entry["id"] = int(entry["id"])
            entry["speciesRepresentations"] = literal_eval(entry["speciesRepresentations"] or "[]")
            entry["albedo_path"] = utils.join_path(TEXTURE_PREFIX, entry["texture"], ALBEDO_TEXTURE_NAME)
            entry["normal_path"] = utils.join_path(TEXTURE_PREFIX, entry["texture"], NORMAL_TEXTURE_NAME)

            del entry["texture"]

            logger.debug("Parsed phytocoenosis with ID {}".format(entry["id"]))
        except ValueError:
            logger.error("One of the types in the json row {} did not have the correct type!"
                         " Please check the specification.".format(entry))
