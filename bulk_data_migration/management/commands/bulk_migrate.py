from django.core.management.base import BaseCommand
import importlib


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            'migration_type',
            nargs=1,
        )

    def handle(self, *args, **kwargs):
        migration_type = kwargs['migration_type'][0]
        migrate = importlib.import_module(
            'bulk_data_migration.{}.migrate'.format(migration_type)
        ).migrate
        migrate()
