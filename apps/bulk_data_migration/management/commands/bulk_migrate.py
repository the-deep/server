from django.core.management.base import BaseCommand
import importlib


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            'arg_list',
            nargs='+',
        )
        parser.add_argument(
            '--filters_file',
            type=str,
            default=None
        )

    def handle(self, *args, **kwargs):
        arg_list = kwargs.pop('arg_list', [])
        migration_type = arg_list[0]
        migrate = importlib.import_module(
            'bulk_data_migration.{}.migrate'.format(migration_type)
        ).migrate
        migrate(*(arg_list[1:]), **kwargs)
