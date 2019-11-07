from django.apps import AppConfig
from django.db.utils import ProgrammingError


class ConnectorConfig(AppConfig):
    name = 'connector'

    def ready(self):
        from connector.models import ConnectorSource
        from .sources.store import source_store
        from utils.common import kebabcase_to_titlecase

        try:
            for key in source_store.keys():
                ConnectorSource.objects.get_or_create(
                    key=key,
                    defaults={'title': kebabcase_to_titlecase(key)},
                )
        except ProgrammingError:
            # Because, ready() is called before the migration to create ConnectorSource table is run
            pass
