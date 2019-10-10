import json
import logging
import os
from datetime import datetime

import fiona
from django.contrib.gis import geos
from django.core.exceptions import ObjectDoesNotExist
from django.core.management import BaseCommand

from assetpos.models import Asset
from location.models import Scenario
from raster.tiles import get_root_tile

logger = logging.getLogger(__name__)

WEBMERCATOR_SRID = 3857


class Command(BaseCommand):
    help = """
    Parses a shp to a fixture which contains positions (instances) of the asset with the given ID.
    """

    def add_arguments(self, parser):
        parser.add_argument("--shapefile", type=str)
        parser.add_argument("--out", type=str)
        parser.add_argument("--asset_id", type=str)
        parser.add_argument("--srid", type=int)
        parser.add_argument("--scenario_id", type=int)

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

        if "asset_id" not in options or not options["asset_id"]:
            logger.error("No asset ID given!")
            return

        if "srid" not in options or not options["srid"]:
            input_srid = None
            logger.warn("No input srid given! Assuming webmercator")
        else:
            input_srid = options["srid"]

        if "scenario_id" not in options or not options["scenario_id"]:
            scenario_id = None
            logger.info("No scenario ID given! Assets will be valid in all scenarios")
        else:
            scenario_id = options["scenario_id"]

        try:
            asset = Asset.objects.get(id=options["asset_id"])
        except ObjectDoesNotExist:
            logger.error("Invalid asset ID!")
            return

        try:
            scenario = Scenario.objects.get(id=scenario_id)
        except ObjectDoesNotExist:
            logger.error("Invalid scenario ID!")
            return

        asset_type = asset.asset_type

        logger.info("Asset name: {}".format(asset.name))
        logger.info("AssetType name: {}".format(asset_type.name))

        if scenario:
            logger.info("Scenario name: {}".format(scenario.name))

        json_data = []

        logger.info("Parsing...")

        # Parse features from the shapefile into a json file in the fixture format
        for feature in fiona.open(options["shapefile"]):
            if input_srid:
                pointstring = geos.Point(*feature["geometry"]["coordinates"], srid=input_srid)
            else:
                pointstring = geos.Point(*feature["geometry"]["coordinates"], srid=WEBMERCATOR_SRID)
                pointstring.transform(WEBMERCATOR_SRID)

            if scenario:
                tile = get_root_tile(scenario)
            else:
                tile = None

            fields = {
                "asset": asset.id,
                "asset_type": asset_type.id,
                "location": str(pointstring),
                "create_stamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.0Z"),
                "tile": tile.id
            }

            json_data.append({"model": "assetpos.AssetPositions", "fields": fields})

        logger.info("Writing the result...")

        # Write the result into a nicely human-readable json fixture
        with open(options["out"], "w+") as outfile:
            outfile.write(json.dumps(json_data, sort_keys=False, indent=4, separators=(",", ": "), ensure_ascii=False))

            logger.info("Success!")
