from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone

from user.models import User
from project.models import Project


class Notification(models.Model):
    class Type(models.TextChoices):
        # Project Joins Notification Types
        PROJECT_JOIN_REQUEST = 'project_join_request', 'Join project request'
        PROJECT_JOIN_REQUEST_ABORT = 'project_join_request_abort', 'Join project request abort'
        PROJECT_JOIN_RESPONSE = 'project_join_response', 'Join project response'
        # Entry Comment Notifications Types
        ENTRY_COMMENT_ADD = 'entry_comment_add', 'Entry Comment Add'
        ENTRY_COMMENT_MODIFY = 'entry_comment_modify', 'Entry Comment Modify'
        ENTRY_COMMENT_ASSIGNEE_CHANGE = 'entry_comment_assignee_change', 'Entry Comment Assignee Change'
        ENTRY_COMMENT_REPLY_ADD = 'entry_comment_reply_add', 'Entry Comment Reply Add'
        ENTRY_COMMENT_REPLY_MODIFY = 'entry_comment_reply_modify', 'Entry Comment Reply Modify'
        ENTRY_COMMENT_RESOLVED = 'entry_comment_resolved', 'Entry Comment Resolved'
        # Entry Comment Review Notifications Types
        ENTRY_REVIEW_COMMENT_ADD = 'entry_review_comment_add', 'Entry Review Comment Add'
        ENTRY_REVIEW_COMMENT_MODIFY = 'entry_review_comment_modify', 'Entry Review Comment Modify'

    class Status(models.TextChoices):
        SEEN = 'seen', 'Seen'
        UNSEEN = 'unseen', 'Unseen'

    receiver = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        default=None
    )
    data = models.JSONField(default=None, blank=True, null=True)
    notification_type = models.CharField(max_length=48, choices=Type.choices)
    status = models.CharField(
        max_length=48,
        choices=Status.choices,
        default=Status.UNSEEN,
    )
    timestamp = models.DateTimeField(
        default=timezone.now,
    )

    def __str__(self):
        return f'{self.notification_type}:: <{self.receiver}> ({self.status})'

    class Meta:
        ordering = ['-timestamp']

    @staticmethod
    def get_for(user):
        return Notification.objects.filter(receiver=user).distinct()


class Assignment(models.Model):
    """
    Assignment Model
    """
    created_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        blank=True, null=True,
        on_delete=models.SET_NULL,
        related_name='created_by',
    )
    created_for = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_for',
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
    )
    is_done = models.BooleanField(default=False)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        ordering = ['-created_at']

    @staticmethod
    def get_for(user):
        return Assignment.objects.filter(
            created_for=user,
        ).distinct()
