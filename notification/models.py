from django.db import models
from django.contrib.postgres.fields import JSONField
from django.utils import timezone

from user.models import User
from project.models import Project


class Notification(models.Model):
    PROJECT_JOIN_REQUEST = 'project_join_request'
    PROJECT_JOIN_RESPONSE = 'project_join_response'
    PROJECT_JOIN_REQUEST_ABORT = 'project_join_request_abort'
    STATUS_SEEN = 'seen'
    STATUS_UNSEEN = 'unseen'

    TYPE_CHOICES = (
        (PROJECT_JOIN_REQUEST, 'Join project request'),
        (PROJECT_JOIN_REQUEST_ABORT, 'Join project request abort'),
        (PROJECT_JOIN_RESPONSE, 'Join project response'),
    )

    STATUS_CHOICES = (
        (STATUS_SEEN, 'Seen'),
        (STATUS_UNSEEN, 'Unseen'),
    )

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
        choices=TYPE_CHOICES,
    )
    data = JSONField(default=None, blank=True, null=True)
    status = models.CharField(
        max_length=48,
        choices=STATUS_CHOICES,
        default=STATUS_UNSEEN,
    )
    timestamp = models.DateTimeField(
        default=timezone.now,
    )

    def __str__(self):
        # TODO
        return 'Notification'

    class Meta:
        ordering = ['-timestamp']

    @staticmethod
    def get_for(user):
        return Notification.objects.filter(
            models.Q(receiver=user)
        ).distinct()
