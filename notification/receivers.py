from django.dispatch import receiver
from django.db.models.signals import post_save

from notification.models import Notification
from project.models import ProjectJoinRequest


@receiver(post_save, sender=ProjectJoinRequest)
def create_notification(sender, instance, created, **kwargs):
    admins = instance.project.get_admins()

    if (created):
        for admin in admins:
            data = {'join_request_id': instance.id}
            Notification.objects.create(
                receiver=admin,
                notification_type=Notification.PROJECT_JOIN_REQUEST,
                project=instance.project,
                data=data,
            )

        return

    # Changing unseen to seen for obsolete action (Not implemented)
    """
    notifications = Notification.objects.filter(
        data__id=instance.id,
        status='unseen',
    )

    for notification in notifications:
        notification.status = 'seen'
        notification.save()
    """

    for admin in admins:
        data = {'join_request_id': instance.id}

        Notification.objects.create(
            receiver=admin,
            notification_type=Notification.PROJECT_JOIN_RESPONSE,
            project=instance.project,
            data=data,
        )
