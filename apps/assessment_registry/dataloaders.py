
from collections import defaultdict
from promise import Promise

from django.utils.functional import cached_property
from utils.graphene.dataloaders import DataLoaderWithContext, WithContextMixin

from .models import AssessmentRegistryOrganization


class AssessmentRegistryOrganizationsLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        qs = AssessmentRegistryOrganization.objects.filter(assessment_registry__in=keys)
        _map = defaultdict(list)
        for org in qs.all():
            _map[org.assessment_registry_id].append(org)
        return Promise.resolve([_map.get(key) for key in keys])


class DataLoaders(WithContextMixin):

    @cached_property
    def stakeholders(self):
        return AssessmentRegistryOrganizationsLoader(context=self.context)
