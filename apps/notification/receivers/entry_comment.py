import logging
from datetime import datetime

from django.dispatch import receiver
from django.db.models.signals import (
    post_save,
    pre_save,
    m2m_changed,
    post_delete
)
from django.db import transaction
from django.conf import settings

from deep.middleware import get_user
from entry.models import EntryComment, EntryCommentText
from entry.serializers import EntryCommentSerializer
from notification.models import Notification, Assignment
from notification.tasks import send_entry_comment_email
from lead.models import Lead

logger = logging.getLogger(__name__)


def send_notifications_for_commit(comment_pk, notification_meta):
    comment = EntryComment.objects.get(pk=comment_pk)

    notification_meta = {
        **notification_meta,
        'project': comment.entry.project,
        'data': EntryCommentSerializer(comment).data,
    }
    related_users = comment.get_related_users()

    for user in related_users:
        # Create DEEP Notification Objects
        Notification.objects.create(
            **notification_meta,
            receiver=user,
        )

        # Send Email Notification
        if settings.TESTING:
            send_entry_comment_email(user.pk, comment.pk)
        else:
            transaction.on_commit(
                lambda: send_entry_comment_email.delay(user.pk, comment.pk)
            )


@receiver(pre_save, sender=EntryComment)
def create_entry_commit_notification(sender, instance, **kwargs):
    created = instance.pk is None
    instance.receiver_created = created
    if created or instance.parent:  # Notification is handled from commit text creation
        return

    meta = {}

    old_comment = EntryComment.objects.get(pk=instance.pk)

    if instance.is_resolved and old_comment.is_resolved != instance.is_resolved:  # Comment is Resolved
        meta['notification_type'] = Notification.ENTRY_COMMENT_RESOLVED
        transaction.on_commit(lambda: send_notifications_for_commit(instance.pk, meta))
        instance.receiver_notification_already_send = True


@receiver(m2m_changed, sender=EntryComment.assignees.through)
def create_entry_commit_notification_post(sender, instance, action, **kwargs):
    receiver_notification_already_send = getattr(instance, 'receiver_notification_already_send', False)
    # Default:False Because when it's patch request with only m2m change, create_entry_commit_notification is not triggered
    created = getattr(instance, 'receiver_created', False)
    if (
        created or action not in ['post_add', 'post_remove'] or instance.parent or receiver_notification_already_send
    ):  # Notification is handled from commit text creation
        return

    meta = {}

    meta['notification_type'] = Notification.ENTRY_COMMENT_ASSIGNEE_CHANGE
    instance.receiver_notification_already_send = True
    transaction.on_commit(lambda: send_notifications_for_commit(instance.pk, meta))


@receiver(post_save, sender=EntryCommentText)
def create_entry_commit_text_notification(sender, instance, created, **kwargs):
    if not created:  # EntryCommentText are never changed, only added
        return

    comment = instance.comment
    meta = {}
    meta['notification_type'] = (
        Notification.ENTRY_COMMENT_REPLY_ADD if comment.parent else Notification.ENTRY_COMMENT_ADD
    )
    if EntryCommentText.objects.filter(comment=comment).count() > 1:
        meta['notification_type'] = (
            Notification.ENTRY_COMMENT_REPLY_MODIFY if comment.parent else Notification.ENTRY_COMMENT_MODIFY
        )

    transaction.on_commit(lambda: send_notifications_for_commit(comment.pk, meta))


@receiver(m2m_changed, sender=Lead.assignee.through)
def lead_assignment_signal(sender, instance, action, **kwargs):
    pk_set = kwargs.get('pk_set', [])
    # Gets the username from the request with a middleware helper
    user = get_user()
    if action == 'post_add' and pk_set and user:
        for receiver in pk_set:
            Assignment.objects.create(
                content_object=instance,
                created_for_id=receiver,
                project=instance.project,
                created_by=user,
            )

    elif action == 'post_remove' and pk_set and user:
        for receiver in pk_set:
            Assignment.objects.filter(lead__id=instance.id, created_for_id=receiver).delete()


@receiver(m2m_changed, sender=EntryComment.assignees.through)
def entrycomment_assignment_signal(sender, instance, action, **kwargs):
    pk_set = kwargs.get('pk_set', [])
    # Gets the username from the request with a middleware helper
    user = get_user()
    if action == 'post_add' and pk_set and user:
        for receiver in pk_set:
            Assignment.objects.create(
                content_object=instance,
                created_for_id=receiver,
                project=instance.entry.project,
                created_by=user,
            )

    elif action == 'post_remove' and pk_set and user:
        for receiver in pk_set:
            Assignment.objects.filter(entry__id=instance.id, created_for_id=receiver).delete()


@receiver(post_delete, sender=Lead)
def delete_assignment(sender, instance, *args, **kwargs):
    lead_id = instance.id
    Assignment.objects.filter(lead__id=lead_id).delete()


@receiver(post_delete, sender=EntryComment)
def delete_assignment(sender, instance, *args, **kwargs):
    entry_id = instance.id
    Assignment.objects.filter(entry__id=entry_id).delete()
