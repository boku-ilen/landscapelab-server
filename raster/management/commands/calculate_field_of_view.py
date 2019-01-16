from django.core.management import BaseCommand


class Command(BaseCommand):
    help = 'calculate the maximum extent of the view of field based on an polygon and the DHM'

    def add_arguments(self, parser):
        parser.add_argument('shapefile', type=str)
        parser.add_argument('project', type=str)
        parser.add_argument('layer', type=str)

    def handle(self, *args, **options):
        pass  # FIXME: ...
