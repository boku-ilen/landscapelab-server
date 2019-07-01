import os

from django.core.management import BaseCommand

import logging
import csv
import json

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """
    This script takes a .shp file, extracts building footprints and saves them to the database
    """

    def add_arguments(self, parser):
        parser.add_argument('--species_representations', type=str)
        parser.add_argument('--phytocoenosis', type=str)
        parser.add_argument('--outfile', type=str)

    def handle(self, *args, **options):
        # Input validation
        if 'species_representations' not in options:
            logger.error("No species representations csv filename given!")
            return

        if 'phytocoenosis' not in options:
            logger.error("No phytocoenosis csv filename given!")
            return

        if 'outfile' not in options:
            logger.error("No output filename given!")
            return

        if not os.path.isfile(options['species_representations']):
            logger.error("Invalid species representations file!")
            return

        if not os.path.isfile(options['phytocoenosis']):
            logger.error("Invalid phytocoenosis file!")
            return

        jsonfile = open(options['outfile'], 'w+')

        species_representation_data = get_csv_as_json(open(options['species_representations'], 'r'), 'SpeciesRepresentation')
        phytocoenosis_data = get_csv_as_json(open(options['phytocoenosis'], 'r'), 'Phytocoenosis')

        json_data = species_representation_data + phytocoenosis_data

        jsonfile.write(json.dumps(json_data, sort_keys=False, indent=4, separators=(',', ': '), ensure_ascii=False))


def get_csv_as_json(csvfile, modelname):
    """Parses a CSV file and returns the data in the Django fixture format.
    The given modelname must match the name of the Django model this data corresponds to."""

    json_data = []

    reader = csv.DictReader(csvfile)

    for row in reader:
        json_data.append({"model": "vegetation.{}".format(modelname), "fields": row})

    return json_data
