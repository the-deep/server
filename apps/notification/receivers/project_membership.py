from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete, pre_save

from notification.models import Notification
from project.models import (
    ProjectJoinRequest,
    ProjectMembership,
    ProjectRole,
)
from project.serializers import ProjectJoinGqSerializer


@receiver(post_save, sender=ProjectJoinRequest)
def create_notification(sender, instance, created, **kwargs):
    admins = instance.project.get_admins()
    data = ProjectJoinGqSerializer(instance).data
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
def update_notification_for_join_request(sender, instance, **kwargs):
    old_notifications = Notification.objects.filter(
        data__id=instance.id
    )

    for notification in old_notifications:
        notification.data['status'] = 'aborted'
        notification.save()

    admins = instance.project.get_admins()
    data = ProjectJoinGqSerializer(instance).data
    data['status'] = 'aborted'
    for admin in admins:
        Notification.objects.create(
            receiver=admin,
            notification_type=Notification.PROJECT_JOIN_REQUEST_ABORT,
            project=instance.project,
            data=data
        )


@receiver(pre_save, sender=ProjectMembership)
def remove_notifications_for_former_project_admin(
        sender, instance, **kwargs):
    admin_roles = ProjectRole.get_admin_roles()

    try:
        old_membership = ProjectMembership.objects.get(id=instance.id)

        if old_membership.role in admin_roles\
                and instance.role not in admin_roles:
            old_notifications = Notification.objects.filter(
                receiver=instance.member,
                project=instance.project
            )
            old_notifications.delete()

        if old_membership.role not in admin_roles\
                and instance.role in admin_roles:

            old_project_join_requests = ProjectJoinRequest.objects.filter(
                project=instance.project,
                status='pending',
            )

            for old_project_join_request in old_project_join_requests:
                Notification.objects.create(
                    receiver=instance.member,
                    notification_type=Notification.PROJECT_JOIN_REQUEST,
                    project=instance.project,
                    data=ProjectJoinGqSerializer(
                        old_project_join_request).data,
                )
    except ProjectMembership.DoesNotExist:
        pass


@receiver(post_save, sender=ProjectMembership)
def create_notifications_for_new_project_admin(
        sender, instance, created, **kwargs):
    if created is True:
        if instance.role in ProjectRole.get_admin_roles():
            old_project_join_requests = ProjectJoinRequest.objects.filter(
                project=instance.project,
                status='pending',
            )

            for old_project_join_request in old_project_join_requests:
                Notification.objects.create(
                    receiver=instance.member,
                    notification_type=Notification.PROJECT_JOIN_REQUEST,
                    project=instance.project,
                    data=ProjectJoinGqSerializer(
                        old_project_join_request).data,
                )
