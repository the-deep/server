
from collections import defaultdict
from promise import Promise

from django.utils.functional import cached_property
from utils.graphene.dataloaders import DataLoaderWithContext, WithContextMixin

from .models import (
    AssessmentRegistryOrganization,
    SummarySubPillarIssue,
)


class AssessmentRegistryOrganizationsLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        qs = AssessmentRegistryOrganization.objects.filter(assessment_registry__in=keys)
        _map = defaultdict(list)
        for org in qs.all():
            _map[org.assessment_registry_id].append(org)
        return Promise.resolve([_map.get(key) for key in keys])


class AssessmentRegistryIssueLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        qs = SummarySubPillarIssue.objects.filter(assessment_registry__in=keys)
        _map = defaultdict(list)
        for issue in qs.all():
            _map[issue.assessment_registry_id].append(issue)
        return Promise.resolve([_map.get(key) for key in keys])


class DataLoaders(WithContextMixin):

    @cached_property
    def stakeholders(self):
        return AssessmentRegistryOrganizationsLoader(context=self.context)

    @cached_property
    def issues(self):
        return AssessmentRegistryIssueLoader(context=self.context)
