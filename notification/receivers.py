from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete

from notification.models import Notification
from project.models import ProjectJoinRequest
from project.serializers import ProjectJoinRequestSerializer


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

    data = {'join_request_id': instance.id}
    for admin in admins:
        Notification.objects.create(
            receiver=admin,
            notification_type=Notification.PROJECT_JOIN_RESPONSE,
            project=instance.project,
            data=data,
        )


@receiver(post_delete, sender=ProjectJoinRequest)
def update_notification(sender, instance, **kwargs):
    admins = instance.project.get_admins()

    for admin in admins:
        Notification.objects.create(
            receiver=admin,
            notification_type=Notification.PROJECT_JOIN_REQUEST_ABORT,
            project=instance.project,
            data=ProjectJoinRequestSerializer(instance).data,
        )
