from itertools import count
from operator import countOf
from django.db import models
from collections import defaultdict
from promise import Promise

from django.utils.functional import cached_property
from utils.graphene.dataloaders import DataLoaderWithContext, WithContextMixin

from .models import (
    AssessmentRegistryOrganization,
    SummaryIssue,
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
        qs = SummaryIssue.objects.filter(
            parent__in=keys
        ).order_by().values('parent').annotate(
            count=models.Count('id')
        ).values_list(
            'parent', 'count'
        )

        print("QS*************************", qs)
        counts = {
            ass_reg_id: count
            for ass_reg_id, count in qs
        }

        return Promise.resolve([counts.get(key, 0) for key in keys])


class AssessmentRegistryIssueChildLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        qs = SummaryIssue.objects.filter(parent__id__in=keys)
        _map = {
            issue.pk: issue
            for issue in qs
        }
        return Promise.resolve([_map.get(key) for key in keys])


class DataLoaders(WithContextMixin):

    @cached_property
    def stakeholders(self):
        return AssessmentRegistryOrganizationsLoader(context=self.context)

    @cached_property
    def issues(self):
        return AssessmentRegistryIssueLoader(context=self.context)

    @cached_property
    def child_issues(self):
        return AssessmentRegistryIssueChildLoader(context=self.context)
