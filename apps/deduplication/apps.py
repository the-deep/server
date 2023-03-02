from django.apps import AppConfig


class DeduplicationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "deduplication"

    def ready(self):
        import deduplication.receivers  # noqa
