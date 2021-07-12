from collections import defaultdict

from promise import Promise

from deep.dataloaders import DataLoaderWithContext

from user.models import User
from .models import (
    UserGroup,
    GroupMembership,
)


class UserGroupMembersLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        membership_qs = GroupMembership.objects.filter(
            # Only fetch for user_group where current user is member + ids (keys)
            group__in=UserGroup.get_for_member(self.context.user).filter(id__in=keys)
        )
        # Users map
        user_qs = User.objects.filter(id__in=membership_qs.values('member'))
        users_map = {u.id: u for u in user_qs}
        # Membership map
        members_map = defaultdict(list)
        for group_id, member_id in membership_qs.values_list('group', 'member'):
            members = users_map.get(member_id)
            members and members_map[group_id].append(members)

        print(keys, members_map)
        return Promise.resolve(
            [members_map[key] for key in keys]
        )
