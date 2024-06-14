from celery import shared_task
from django.db import transaction
from entry.models import EntryComment
from quality_assurance.models import EntryReviewComment
from user.models import EmailCondition, User
from user.utils import send_mail_to_user

from deep.permalinks import Permalink

from .models import Notification


@shared_task
def send_entry_comment_email(user_id, comment_id):
    user = User.objects.get(pk=user_id)
    comment = EntryComment.objects.get(pk=comment_id)
    send_mail_to_user(
        user,
        EmailCondition.EMAIL_COMMENT,
        context={
            "notification_type": Notification.Type.ENTRY_COMMENT_ADD,
            "Notification": Notification,
            "comment": comment,
            "assignees_display": ", ".join(assignee.profile.get_display_name() for assignee in comment.assignees.all()),
            "entry_comment_client_url": Permalink.ientry_comments(comment.entry),
        },
        subject_template_name="entry/comment_notification_email.txt",
        email_template_name="entry/comment_notification_email.html",
    )


@shared_task
def send_entry_review_comment_email(user_id, comment_id, notification_type):
    user = User.objects.get(pk=user_id)
    comment = EntryReviewComment.objects.get(pk=comment_id)
    send_mail_to_user(
        user,
        EmailCondition.EMAIL_COMMENT,
        context={
            "Notification": Notification,
            "CommentType": EntryReviewComment.CommentType,
            "notification_type": notification_type,
            "comment": comment,
            "entry_comment_client_url": Permalink.ientry_comment(comment),
        },
        subject_template_name="entry/review_comment_notification_email.txt",
        email_template_name="entry/review_comment_notification_email.html",
    )


def send_notifications_for_comment(comment_pk, meta):
    """
    This is for new Entry Review Comment
    """
    comment = EntryReviewComment.objects.get(pk=comment_pk)

    text_changed = meta.pop("text_changed")
    new_mentioned_users = meta.pop("new_mentioned_users", [])
    if text_changed:
        related_users = comment.get_related_users()
    else:
        related_users = new_mentioned_users

    from quality_assurance.serializers import EntryReviewCommentNotificationSerializer

    for user in related_users:
        # Create DEEP Notification Objects
        Notification.objects.create(
            **meta,
            project=comment.entry.project,
            data=EntryReviewCommentNotificationSerializer(comment).data,
            receiver=user,
        )

        # Send Email Notification
        transaction.on_commit(
            lambda: send_entry_review_comment_email.delay(
                user.pk,
                comment.pk,
                meta["notification_type"],
            )
        )
