from django.utils.functional import cached_property

from deep.dataloaders import WithContextMixin
from user.dataloaders import DataLoaders as UserDataLoaders
from user_group.dataloaders import DataLoaders as UserGroupDataLoaders


class DataLoaders(WithContextMixin):
    @cached_property
    def user_group(self):
        return UserGroupDataLoaders(context=self.context)

    @cached_property
    def user(self):
        return UserDataLoaders(context=self.context)


class GQLContext:
    def __init__(self, request):
        self.request = request

    @property
    def user(self):
        return self.request.user

    @cached_property
    def dl(self):
        return DataLoaders(context=self)
