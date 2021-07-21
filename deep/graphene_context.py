from django.utils.functional import cached_property

from deep.permissions import ProjectPermissions as PP
from deep.dataloaders import GlobalDataLoaders


class GQLContext:
    def __init__(self, request):
        self.request = request
        self.active_project = self.request.active_project = None
        self.permissions = []

    def set_active_project(self, project):
        self.active_project = self.request.active_project = project
        self.permissions = PP.get_permissions(project.current_user_role)

    @property
    def user(self):
        return self.request.user

    @cached_property
    def dl(self):
        return GlobalDataLoaders(context=self)
