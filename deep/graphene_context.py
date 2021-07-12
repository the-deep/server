from django.utils.functional import cached_property

from user_group.dataloaders import UserGroupMembersLoader


class GQLContext:
    def __init__(self, request):
        self.request = request

    @property
    def user(self):
        return self.request.user

    @cached_property
    def dl_user_group_members(self):
        return UserGroupMembersLoader(context=self)
