from django.apps import AppConfig


class GeoConfig(AppConfig):
    name = 'geo'

    def ready(self):
        import utils.db.functions  # noqa
