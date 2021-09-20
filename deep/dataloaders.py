from django.utils.functional import cached_property

from utils.graphene.dataloaders import WithContextMixin

from project.dataloaders import DataLoaders as ProjectDataLoaders
from user.dataloaders import DataLoaders as UserDataLoaders
from user_group.dataloaders import DataLoaders as UserGroupDataLoaders
from lead.dataloaders import DataLoaders as LeadDataLoaders
from entry.dataloaders import DataLoaders as EntryDataloaders
from organization.dataloaders import DataLoaders as OrganizationDataLoaders
from analysis_framework.dataloaders import DataLoaders as AfDataloaders
from quality_assurance.dataloaders import DataLoaders as QADataLoaders


class GlobalDataLoaders(WithContextMixin):
    @cached_property
    def user_group(self):
        return UserGroupDataLoaders(context=self.context)

    @cached_property
    def user(self):
        return UserDataLoaders(context=self.context)

    @cached_property
    def lead(self):
        return LeadDataLoaders(context=self.context)

    @cached_property
    def entry(self):
        return EntryDataloaders(context=self.context)

    @cached_property
    def organization(self):
        return OrganizationDataLoaders(context=self.context)

    @cached_property
    def analysis_framework(self):
        return AfDataloaders(context=self.context)

    @cached_property
    def project(self):
        return ProjectDataLoaders(context=self.context)

    @cached_property
    def quality_assurance(self):
        return QADataLoaders(context=self.context)
