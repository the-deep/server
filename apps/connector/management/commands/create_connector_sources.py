from django.core.management.base import BaseCommand

from connector.models import ConnectorSource
from connector.sources.store import source_store
from utils.common import replace_ns, kebabcase_to_titlecase


class Command(BaseCommand):
    """
    This is a command to add connector sources if not already created.
    """
    def handle(self, *args, **kwargs):
        print('Creating connector sources that are not created')
        for key in source_store.keys():
            obj, created = ConnectorSource.objects.get_or_create(
                key=key,
                defaults={'title': kebabcase_to_titlecase(key)},
            )
            if created:
                print(f'Created source for {key}')
            else:
                print(f'Source for {key} already exists.')
        print('Done')
