from django.dispatch import receiver
from django.db.models.signals import post_save

from project.models import Project, ProjectMembership
from user.models import User, Profile


def assign_to_default_project(user):
    """
    Get a default project if any and add the user as its member
    """
    default_projects = Project.objects.filter(is_default=True)
    for default_project in default_projects:
        ProjectMembership.objects.create(
            member=user,
            project=default_project,
            role='normal',
        )


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, created, **kwargs):
    """
    Signal to auto create or save user profile instance whenever
    the user is saved.
    """
    if created or Profile.objects.filter(user=instance).count() == 0:
        Profile.objects.create(user=instance)
        assign_to_default_project(instance)
    else:
        instance.profile.save()
