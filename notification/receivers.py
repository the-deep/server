from django.dispatch import receiver
from django.db.models.signals import post_save

from notification.models import Notification
from project.models import ProjectJoinRequest


@receiver(post_save, sender=ProjectJoinRequest)
def create_notification(sender, instance, created, **kwargs):
    if (created):
        admins = instance.project.get_admins()

        for admin in admins:
            Notification.objects.create(
                receiver=admin,
                notification_type='project_join',
                project=instance.project,
                status='unseen',
            )

