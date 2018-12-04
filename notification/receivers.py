from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete

from notification.models import Notification
from project.models import ProjectJoinRequest
from project.serializers import ProjectJoinRequestSerializer


@receiver(post_save, sender=ProjectJoinRequest)
def create_notification(sender, instance, created, **kwargs):
    admins = instance.project.get_admins()
    data = ProjectJoinRequestSerializer(instance).data

    if (created):
        for admin in admins:
            Notification.objects.create(
                receiver=admin,
                notification_type=Notification.PROJECT_JOIN_REQUEST,
                project=instance.project,
                data=data,
            )
        return

    # notifiy the requester as well
    if instance.status in ['accepted', 'rejected']:
        Notification.objects.create(
            receiver=instance.requested_by,
            notification_type=Notification.PROJECT_JOIN_RESPONSE,
            project=instance.project,
            data=data,
        )

    old_notifications = Notification.objects.filter(
        data__id=instance.id
    )

    for notification in old_notifications:
        notification.data = data
        notification.save()

    for admin in admins:
        Notification.objects.create(
            receiver=admin,
            notification_type=Notification.PROJECT_JOIN_RESPONSE,
            project=instance.project,
            data=data,
        )


@receiver(post_delete, sender=ProjectJoinRequest)
def update_notification(sender, instance, **kwargs):
    old_notifications = Notification.objects.filter(
        data__id=instance.id
    )

    for notification in old_notifications:
        notification.data['status'] = 'aborted'
        notification.save()

    admins = instance.project.get_admins()
    data = ProjectJoinRequestSerializer(instance).data
    data['status'] = 'aborted'
    for admin in admins:
        Notification.objects.create(
            receiver=admin,
            notification_type=Notification.PROJECT_JOIN_REQUEST_ABORT,
            project=instance.project,
            data=data
        )
