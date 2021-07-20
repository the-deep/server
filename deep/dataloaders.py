from django.utils.functional import cached_property

from utils.graphene.dataloaders import WithContextMixin

from user.dataloaders import DataLoaders as UserDataLoaders
from user_group.dataloaders import DataLoaders as UserGroupDataLoaders
from lead.dataloaders import DataLoaders as LeadDataLoaders
from organization.dataloaders import DataLoaders as OrganizationDataLoaders


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
    def organization(self):
        return OrganizationDataLoaders(context=self.context)
