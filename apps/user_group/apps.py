from django.apps import AppConfig


class UserGroupConfig(AppConfig):
    name = 'user_group'

    def ready(self):
        from . import receivers # noqa
