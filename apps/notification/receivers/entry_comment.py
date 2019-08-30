from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
from django.db import transaction

from entry.models import EntryComment, EntryCommentText
from entry.serializers import EntryCommentSerializer
from notification.models import Notification
from notification.tasks import send_entry_comment_email

import logging

logger = logging.getLogger(__name__)


def send_notifications_for_commit(comment, notification_meta):
    related_users = comment.get_related_users()
    for user in related_users:
        # Create DEEP Notification Objects
        Notification.objects.create(
            **notification_meta,
            receiver=user,
        )
        # Send Email Notification
        transaction.on_commit(
            lambda: send_entry_comment_email.delay(user.pk, comment.pk)
        )


@receiver(pre_save, sender=EntryComment)
def create_entry_commit_notification(sender, instance, **kwargs):
    meta = {
        'project': instance.entry.project,
        'data': EntryCommentSerializer(instance).data,
    }

    created = instance.pk is None
    if created or instance.parent:  # Notification is handled from commit text creation
        return

    old_comment = EntryComment.objects.get(pk=instance.pk)
    if instance.is_resolved and old_comment.is_resolved != instance.is_resolved:  # Comment is Resolved
        meta['notification_type'] = Notification.ENTRY_COMMENT_RESOLVED
    elif old_comment.assignee != instance.assignee:  # Assignee is changed
        meta['notification_type'] = Notification.ENTRY_COMMENT_ASSIGNEE_CHANGE

    if meta.get('notification_type'):
        send_notifications_for_commit(instance, meta)


@receiver(post_save, sender=EntryCommentText)
def create_entry_commit_text_notification(sender, instance, created, **kwargs):
    if not created:  # EntryCommentText are never changed, only added
        return

    comment = instance.comment
    meta = {
        'project': comment.entry.project,
        'data': EntryCommentSerializer(comment).data,
    }
    meta['notification_type'] = Notification.ENTRY_COMMENT_REPLY_ADD\
        if comment.parent else Notification.ENTRY_COMMENT_ADD
    if EntryCommentText.objects.filter(comment=comment).count() > 1:
        meta['notification_type'] = Notification.ENTRY_COMMENT_REPLY_MODIFY\
            if comment.parent else Notification.ENTRY_COMMENT_MODIFY

    send_notifications_for_commit(comment, meta)
