from django.db import models
from django.dispatch import receiver

from user.models import User
from project.models import (
    ProjectMembership,
    ProjectUserGroupMembership,
    ProjectJoinRequest,
)


@receiver(models.signals.post_save, sender=ProjectUserGroupMembership)
def refresh_project_memberships_usergroup_modified(sender, instance, **kwargs):
    project = instance.project
    user_group = instance.usergroup

    existing_members = ProjectMembership.objects.filter(
        project=project,
        linked_group=user_group,
    )
    existing_members.update(role=instance.role, badges=instance.badges)

    project_ug_members = User.objects.filter(usergroup__project=project)
    new_users = project_ug_members.difference(project.get_all_members()).\
        distinct()
    for user in new_users:
        project.add_member(user, role=instance.role, linked_group=user_group, badges=instance.badges)


@receiver(models.signals.pre_delete, sender=ProjectUserGroupMembership)
def refresh_project_memberships_usergroup_removed(sender, instance, **kwargs):
    project = instance.project
    user_group = instance.usergroup

    remove_memberships = ProjectMembership.objects.filter(
        project=project,
        linked_group=user_group,
    )

    for membership in remove_memberships:
        other_user_groups = membership.get_user_group_options().exclude(
            id=user_group.id
        )
        if other_user_groups.count() > 0:
            membership.linked_group = other_user_groups.first()
            membership.save()
        else:
            membership.delete()


# Whenever a member is saved, if there is a pending request to join
# same project by same user, accept that request.
@receiver(models.signals.post_save, sender=ProjectMembership)
def on_membership_saved(sender, **kwargs):
    # if kwargs.get('created'):
    instance = kwargs.get('instance')
    ProjectJoinRequest.objects.filter(
        project=instance.project,
        requested_by=instance.member,
        status='pending',
    ).update(
        status='accepted',
        responded_by=instance.added_by,
        responded_at=instance.joined_at,
    )
