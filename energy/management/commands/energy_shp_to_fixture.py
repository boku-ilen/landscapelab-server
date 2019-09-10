import os
import traceback

from django.contrib.gis import geos
from django.core.management import BaseCommand

import logging
import json
import fiona

logger = logging.getLogger(__name__)

WEBMERCATOR_SRID = 3857

# this maps the asset_type id to the field name to use
map_asset_type_to_field = {
    3: "kWhm2",  # pv
    2: "prod_mwh"  # wind
}


class Command(BaseCommand):
    help = """
    Parses a shp to a fixture for energy data
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

        if "asset_type_id" not in options or not options["asset_type_id"]:
            logger.info("no asset type id given!")
            return
        else:
            asset_type_id = options["asset_type_id"]

        if "srid" not in options or not options["srid"]:
            input_srid = WEBMERCATOR_SRID
            logger.info("No input srid given! Assuming the default of {}".format(input_srid))
        else:
            input_srid = options["srid"]

        logger.info("Parsing...")

        # Initialize the json_data with a generic line type
        json_data = []
        error_count = 0

        # Parse features from the shapefile into a json file in the fixture format
        for feature in fiona.open(options["shapefile"]):

            try:
                # Convert the LineString from the original srid to WebMercator
                polygon = geos.Polygon(*feature["geometry"]["coordinates"], srid=input_srid)
                polygon.transform(WEBMERCATOR_SRID)

                fields = {
                    "asset_type": asset_type_id,
                    "energy_production": feature["properties"][map_asset_type_to_field[asset_type_id]],
                    "polygon": str(polygon)
                }
                json_data.append({"model": "energy.EnergyLocation", "fields": fields})

            except Exception:
                logger.error("Error while converting LineString:")
                traceback.print_exc()

                error_count += 1

        if error_count > 0:
            logger.error("Encountered {} errors while parsing, this means that {} entries are now missing!"
                         .format(error_count, error_count))

        logger.info("Writing the result...")

        # Write the result into a nicely human-readable json fixture
        with open(options["out"], "w+") as outfile:
            outfile.write(json.dumps(json_data, sort_keys=False, indent=4, separators=(",", ": "), ensure_ascii=False))

            logger.info("Success!")
