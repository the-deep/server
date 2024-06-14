from django.apps import AppConfig


def device_classes():
    """
    Returns an iterable of all loaded device models.
    """
    from django.apps import apps
    from django_otp.models import Device

    for config in apps.get_app_configs():
        for model in config.get_models():
            if issubclass(model, Device) and not model._meta.proxy:
                yield model


class UserConfig(AppConfig):
    name = "user"
    verbose_name = "[DEEP] Authentication and Authorization"

    def ready(self):
        import django_otp
        import user.receivers  # noqa

        # Override to avoid capturing proxy models
        django_otp.device_classes = device_classes
