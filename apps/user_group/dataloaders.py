from collections import defaultdict
from promise import Promise
from django.utils.functional import cached_property

from utils.graphene.dataloaders import DataLoaderWithContext, WithContextMixin

from .models import (
    UserGroup,
    GroupMembership,
)


class UserGroupMembershipsLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        membership_qs = GroupMembership.objects.filter(
            # Only fetch for user_group where current user is member + ids (keys)
            group__in=UserGroup.get_for_member(self.context.user).filter(id__in=keys)
        ).select_related('member', 'added_by')
        # Membership map
        memberships_map = defaultdict(list)
        for membership in membership_qs:
            memberships_map[membership.group_id].append(membership)
        return Promise.resolve([memberships_map[key] for key in keys])


class UserGroupCurrentUserRoleLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        membership_qs = GroupMembership.objects\
            .filter(group__in=keys, member=self.context.user)\
            .values_list('group_id', 'role')
        # Role map
        role_map = {}
        for group_id, role in membership_qs:
            role_map[group_id] = role
        return Promise.resolve([role_map.get(key) for key in keys])


class DataLoaders(WithContextMixin):
    @cached_property
    def memberships(self):
        return UserGroupMembershipsLoader(context=self.context)

    @cached_property
    def current_user_role(self):
        return UserGroupCurrentUserRoleLoader(context=self.context)
