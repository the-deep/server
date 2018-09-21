from django.core.management.base import BaseCommand
import importlib


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            'arg_list',
            nargs='+',
        )

    def handle(self, *args, **kwargs):
        migration_type = kwargs['arg_list'][0]
        migrate = importlib.import_module(
            'bulk_data_migration.{}.migrate'.format(migration_type)
        ).migrate
        migrate(*(kwargs['arg_list'][1:]))
