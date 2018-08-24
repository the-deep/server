from django.dispatch import receiver
from django.db.models.signals import post_save, pre_delete

from project.models import Project, ProjectMembership
from user_group.models import UserGroup, GroupMembership


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
        # Create memberships, only if this is not signal from delete
        if kwargs.get('delete', False) is False:
            project_members = project.get_all_members()
            new_users = user_group_members.difference(project_members)
            for user in new_users:
                project.add_member(user)

        direct_members = project.get_direct_members()

        remove_members = project_members\
            .exclude(groupmembership__group__project=project)\
            .difference(direct_members)\
            .distinct()
        remove_members = list(remove_members.values_list('id', flat=True))
        # Now remove memberships
        ProjectMembership.objects.filter(
            member__id__in=remove_members).delete()


@receiver(pre_delete, sender=GroupMembership)
def refresh_project_memberships_usergroup_deleted(sender, instance, **kwargs):
    """
    Update project memberships when a usergroup is deleted.
    @instance: UserGroup instance
    NOTE: signal should be fired as pre_delete operation
    """
    user_group = instance.group
    projects = Project.objects.filter(user_groups=user_group)
    user_group_members = user_group.members.all()

    for project in projects:
        direct_members = project.get_direct_members()
        # get all usergroups except this usergroup
        other_ugs = UserGroup.objects.exclude(id=user_group.id)
        remove_members = user_group_members\
            .exclude(groupmembership__group__in=other_ugs)\
            .difference(direct_members)
        remove_members = list(remove_members.values_list('id', flat=True))
        # Now remove memberships
        ProjectMembership.objects.filter(
            member__in=remove_members,
            project=project
        ).delete()
