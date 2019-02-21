from django.apps import AppConfig


class TabularConfig(AppConfig):
    name = 'tabular'

    def ready(self):
        import tabular.receivers  # noqa
