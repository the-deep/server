from promise import Promise
from django.utils.functional import cached_property
from django.db.models import F

from utils.graphene.dataloaders import DataLoaderWithContext, WithContextMixin

from gallery.models import File


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


class DataLoaders(WithContextMixin):
    @cached_property
    def logo(self):
        return LogoLoader(context=self.context)
