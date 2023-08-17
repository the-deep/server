from promise import Promise
from django.utils.functional import cached_property

from utils.graphene.dataloaders import DataLoaderWithContext, WithContextMixin

from gallery.models import File


class GalleryFileLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        qs = File.objects.filter(pk__in=keys)
        _map = {
            item.pk: item
            for item in qs
        }
        return Promise.resolve([_map.get(key) for key in keys])


class DataLoaders(WithContextMixin):
    @cached_property
    def file(self):
        return GalleryFileLoader(context=self.context)
