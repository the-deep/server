from django.utils.functional import cached_property

from deep.dataloaders import WithContextMixin
from deep.permissions import ProjectPermissions as PP
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
        self.active_project = None
        self.permissions = []

    def set_active_project(self, project):
        self.active_project = project
        self.permissions = PP.get_permissions(project.current_user_role)

    @property
    def user(self):
        return self.request.user

    @cached_property
    def dl(self):
        return DataLoaders(context=self)
