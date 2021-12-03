from promise import Promise
from django.utils.functional import cached_property
from django.db.models import F

from utils.graphene.dataloaders import DataLoaderWithContext, WithContextMixin

from gallery.models import File

from .models import Organization


class LogoLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        file_qs = File.objects\
            .annotate(organization_id=F('organization'))\
            .filter(organization__in=keys)
        _map = {
            file.organization_id: file
            for file in file_qs
        }
        return Promise.resolve([_map.get(key) for key in keys])


class OrganizationLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        qs = Organization.objects.filter(id__in=keys)
        _map = {
            org.pk: org for org in qs
        }
        return Promise.resolve([_map.get(key) for key in keys])


class ParentOrganizationLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        qs = Organization.objects.filter(id__in=keys).only('id', 'title')
        _map = {
            org.pk: org for org in qs
        }
        return Promise.resolve([_map.get(key) for key in keys])


class DataLoaders(WithContextMixin):
    @cached_property
    def logo(self):
        return LogoLoader(context=self.context)

    @cached_property
    def organization(self):
        return OrganizationLoader(context=self.context)

    @cached_property
    def parent_organization(self):
        return ParentOrganizationLoader(context=self.context)
