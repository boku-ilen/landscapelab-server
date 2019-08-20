import os
import traceback

from django.contrib.gis import geos
from django.core.management import BaseCommand

import logging
import json
import fiona

logger = logging.getLogger(__name__)

DEFAULT_WIDTH_FIELD_NAME = "WIDTH"
DEFAULT_INPUT_SRID = 4326
WEBMERCATOR_SRID = 3857

# TODO: Only needed until we properly define and/or classify line types
DEFAULT_LINE_TYPE_FIELDS = {
    "id": 1,
    "name": "Street",
    "width": 4.0,
    "display_radius": 1000
}


class Command(BaseCommand):
    help = """
    Parses a shp to a fixture for linear data. Currently only works with streets.
    """

    def add_arguments(self, parser):
        parser.add_argument("--shapefile", type=str)
        parser.add_argument("--out", type=str)
        parser.add_argument("--width_field_name", type=str)
        parser.add_argument("--srid", type=int)

    def handle(self, *args, **options):
        # Validate the arguments
        if "shapefile" not in options or not options["shapefile"]:
            logger.error("No shapefile given!")
            return

        if not os.path.isfile(options["shapefile"]):
            logger.error("Invalid shapefile path!")
            return

        if "out" not in options or not options["out"]:
            logger.error("No output path given!")
            return

        if "width_field_name" not in options or not options["width_field_name"]:
            width_field_name = DEFAULT_WIDTH_FIELD_NAME
            logger.info("No width field name given, using the default of {}".format(DEFAULT_WIDTH_FIELD_NAME))
        else:
            width_field_name = options["width_field_name"]

        if "srid" not in options or not options["srid"]:
            input_srid = DEFAULT_INPUT_SRID
            logger.warn("No input srid given! Assuming the default of {}".format(DEFAULT_INPUT_SRID))
        else:
            input_srid = options["srid"]

        # Initialize the json_data with a generic line type
        # TODO: Expand! Make customizable with options and/or by reading and classifying from the shapefile
        json_data = [{"model": "linear.LineType", "fields": DEFAULT_LINE_TYPE_FIELDS}]

        logger.info("Parsing...")

        # Parse features from the shapefile into a json file in the fixture format
        for feature in fiona.open(options["shapefile"]):
            # The width field is -1 for some entries. Since those are very minor roads such as bike lanes, we ignore
            # them. TODO: Can we really just ignore them or should we handle them differently?
            if feature["properties"][width_field_name] < 0:
                continue

            try:
                # Convert the LineString from the original srid to WebMercator
                linestring = geos.LineString(*feature["geometry"]["coordinates"], srid=input_srid)
                linestring.transform(WEBMERCATOR_SRID)

                fields = {
                    "type": 1,  # TODO: Change once we use more types
                    "width": feature["properties"][width_field_name],
                    "line": str(linestring)}

                json_data.append({"model": "linear.LineSegment", "fields": fields})
            except Exception:
                # FIXME: I get errors for some entries, almost exclusively "TypeError: Dimension mismatch".
                #  What does it mean and how should we handle it?
                logger.error("Error while converting LineString:")
                traceback.print_exc()

        logger.info("Writing the result...")

        # Write the result into a nicely human-readable json fixture
        with open(options["out"], "w+") as outfile:
            outfile.write(json.dumps(json_data, sort_keys=False, indent=4, separators=(",", ": "), ensure_ascii=False))

            logger.info("Success!")
