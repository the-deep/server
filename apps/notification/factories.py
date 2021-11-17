from factory.django import DjangoModelFactory

from notification.models import (
    Notification,
)


class NotificationFactory(DjangoModelFactory):
    class Meta:
        model = Notification
