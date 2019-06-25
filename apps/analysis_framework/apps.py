from django.apps import AppConfig


class AnalysisFrameworkConfig(AppConfig):
    name = 'analysis_framework'

    def ready(self):
        from . import receivers # noqa
