from django.utils.functional import cached_property

from deep.permissions import (
    ProjectPermissions as PP,
    AnalysisFrameworkPermissions as AfP,
)
from deep.dataloaders import GlobalDataLoaders


class GQLContext:
    def __init__(self, request):
        self.request = request
        # Project
        self.active_project = self.request.active_project = None
        self.project_permissions = []
        # Analysis Framework
        self.active_af = self.request.active_af = None
        self.af_permissions = []

    def set_active_project(self, project):
        self.active_project = self.request.active_project = project
        self.project_permissions = PP.get_permissions(project.current_user_role)

    def set_active_af(self, af):
        self.active_af = self.request.active_af = af
        self.af_permissions = AfP.get_permissions(af.current_user_role)

    @property
    def user(self):
        return self.request.user

    @cached_property
    def dl(self):
        return GlobalDataLoaders(context=self)
