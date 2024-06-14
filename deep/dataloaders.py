from analysis.dataloaders import DataLoaders as AnalysisDataLoaders
from analysis_framework.dataloaders import DataLoaders as AfDataloaders
from assessment_registry.dataloaders import DataLoaders as AssessmentRegistryDataLoaders
from assisted_tagging.dataloaders import DataLoaders as AssistedTaggingLoaders
from django.utils.functional import cached_property
from entry.dataloaders import DataLoaders as EntryDataloaders
from gallery.dataloaders import DataLoaders as DeepGalleryDataLoaders
from geo.dataloaders import DataLoaders as GeoDataLoaders
from lead.dataloaders import DataLoaders as LeadDataLoaders
from notification.dataloaders import DataLoaders as AssignmentLoaders
from organization.dataloaders import DataLoaders as OrganizationDataLoaders
from project.dataloaders import DataLoaders as ProjectDataLoaders
from quality_assurance.dataloaders import DataLoaders as QADataLoaders
from unified_connector.dataloaders import DataLoaders as UnifiedConnectorDataLoaders
from user.dataloaders import DataLoaders as UserDataLoaders
from user_group.dataloaders import DataLoaders as UserGroupDataLoaders

from utils.graphene.dataloaders import WithContextMixin


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

    @cached_property
    def geo(self):
        return GeoDataLoaders(context=self.context)

    @cached_property
    def unified_connector(self):
        return UnifiedConnectorDataLoaders(context=self.context)

    @cached_property
    def analysis(self):
        return AnalysisDataLoaders(context=self.context)

    @cached_property
    def assessment_registry(self):
        return AssessmentRegistryDataLoaders(context=self.context)

    @cached_property
    def deep_gallery(self):
        return DeepGalleryDataLoaders(context=self.context)

    @cached_property
    def assisted_tagging(self):
        return AssistedTaggingLoaders(context=self.context)

    @cached_property
    def notification(self):
        return AssignmentLoaders(context=self.context)
