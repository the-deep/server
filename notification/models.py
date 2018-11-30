from django.db import models
from django.contrib.postgres.fields import JSONField

from user_resource.models import UserResource
from user.models import User
from project.models import Project

NOTIFICATION_TYPE_CHOICES = (
    ('project_join', 'Join project'),
)

NOTIFICATION_STATUS_CHOICES = (
    ('seen', 'Seen'),
    ('unseen', 'Unseen'),
)


class Notification(UserResource):
    receiver = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        default=None
    )
    notification_type = models.CharField(
        max_length=48,
        choices=NOTIFICATION_TYPE_CHOICES,
    )
    data = JSONField(default=None, blank=True, null=True)
    status = models.CharField(
        max_length=48,
        choices=NOTIFICATION_STATUS_CHOICES,
    )

    @staticmethod
    def get_for(user):
        return Notification.objects.filter(
            models.Q(receiver=user)
        ).distinct()
