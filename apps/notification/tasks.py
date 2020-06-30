from celery import shared_task

from entry.models import EntryComment
from user.models import User, Profile
from user.utils import send_mail_to_user

from .models import Notification


@shared_task
def send_entry_comment_email(user_id, comment_id):
    user = User.objects.get(pk=user_id)
    comment = EntryComment.objects.get(pk=comment_id)
    send_mail_to_user(
        user, Profile.E_EMAIL_COMMENT,
        context={
            'notification_type': Notification.ENTRY_COMMENT_ADD,
            'Notification': Notification,
            'comment': comment,
            'assignees_display': ', '.join(
                assignee.profile.get_display_name() for assignee in comment.assignees.all()
            ),
        },
        subject_template_name='entry/comment_notification_email.txt',
        email_template_name='entry/comment_notification_email.html',
    )
