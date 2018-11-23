from django.dispatch import receiver
from django.db.models.signals import post_save, pre_delete

from project.models import (
    Project,
    ProjectMembership,
    ProjectUserGroupMembership,
)
from user_group.models import GroupMembership


@receiver(post_save, sender=GroupMembership)
def refresh_project_memberships_usergroup_updated(sender, instance, **kwargs):
    """
    Update project memberships when a usergroup is updated
    @instance: GroupMembership instance
    """
    user_group = instance.group
    projects = Project.objects.filter(user_groups=user_group)
    user_group_members = user_group.members.all()
    for project in projects:
        project_group_membership = ProjectUserGroupMembership.objects.get(
            project=project,
            usergroup=user_group,
        )

        # Create memberships, only if this is not signal from delete
        if kwargs.get('delete', False) is False:
            project_members = project.get_all_members()
            new_users = user_group_members.difference(project_members)
            for user in new_users:
                project.add_member(user, role=project_group_membership.role)

        remove_memberships = ProjectMembership.objects.filter(
            project=project,
            linked_group=user_group,
        ).exclude(member__in=user_group_members)

        for membership in remove_memberships:
            other_user_groups = membership.get_user_group_options().exclude(
                id=user_group.id
            )
            if other_user_groups.count() > 0:
                membership.linked_group = other_user_groups.first()
                membership.save()
            else:
                membership.delete()


@receiver(pre_delete, sender=GroupMembership)
def refresh_project_memberships_usergroup_deleted(sender, instance, **kwargs):
    """
    Update project memberships when users removed from usergroups
    @sender: many_to_many field
    """

    user_group = instance.group
    projects = Project.objects.filter(user_groups=user_group)
    for project in projects:
        membership = project.projectmembership_set.filter(
            member=instance.member,
            linked_group=user_group,
        ).first()

        if not membership:
            continue

        other_user_groups = membership.get_user_group_options().exclude(
            id=user_group.id
        )
        if other_user_groups.count() > 0:
            membership.linked_group = other_user_groups.first()
            membership.save()
        else:
            membership.delete()
