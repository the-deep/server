from factory.django import DjangoModelFactory

from notification.models import (
    Assignment,
    Notification,
)


class NotificationFactory(DjangoModelFactory):
    class Meta:
        model = Notification


class AssignmentFactory(DjangoModelFactory):
    class Meta:
        model = Assignment
