from django.utils.functional import cached_property

from deep.dataloaders import GlobalDataLoaders
from deep.permissions import AnalysisFrameworkPermissions as AfP
from deep.permissions import ProjectPermissions as PP
from deep.permissions import UserGroupPermissions as UgP


class GQLContext:
    def __init__(self, request):
        self.request = request
        # Project
        self.active_project = self.request.active_project = None
        self.project_permissions = self.request.project_permissions = []
        # AnalysisFramework
        self.active_af = self.request.active_af = None
        self.af_permissions = []
        # UserGroup
        self.active_ug = self.request.active_ug = None
        self.ug_permissions = []

    def set_active_project(self, project):
        self.active_project = self.request.active_project = project
        self.project_permissions = self.request.project_permissions = PP.get_permissions(project, self.request.user)

    def set_active_af(self, af):
        self.active_af = self.request.active_af = af
        self.af_permissions = AfP.get_permissions(af.get_current_user_role(self.request.user))

    def set_active_usergroup(self, user_group):
        self.active_ug = self.request.active_ug = user_group
        self.ug_permissions = self.request.ug_permissions = UgP.get_permissions(
            user_group.get_current_user_role(self.request.user)
        )

    @property
    def user(self):
        return self.request.user

    @cached_property
    def dl(self):
        return GlobalDataLoaders(context=self)
