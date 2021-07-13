from collections import defaultdict
from asgiref.sync import sync_to_async

from deep.dataloaders import DataLoaderWithContext

from .models import (
    UserGroup,
    GroupMembership,
)


class UserGroupMembersLoader(DataLoaderWithContext):
    # https://github.com/graphql-python/graphene-django/issues/705#issuecomment-670511313
    @sync_to_async
    def fetch_from_db(self, keys):
        membership_qs = GroupMembership.objects.filter(
            # Only fetch for user_group where current user is member + ids (keys)
            group__in=UserGroup.get_for_member(self.context.user).filter(id__in=keys)
        ).select_related('member')
        # Membership map
        members_map = defaultdict(list)
        for membership in membership_qs:
            members_map[membership.group_id].append(membership.member)

        print(keys, members_map)
        return [members_map[key] for key in keys]

    async def batch_load_fn(self, keys):
        return await self.fetch_from_db(keys)
