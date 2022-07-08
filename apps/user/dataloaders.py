from promise import Promise
from django.utils.functional import cached_property

from utils.graphene.dataloaders import DataLoaderWithContext, WithContextMixin

from .models import Profile


class UserProfileLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        profile_qs = Profile.objects.filter(user__in=keys).select_related()
        _map = {
            profile.user_id: profile
            for profile in profile_qs
        }
        return Promise.resolve([_map.get(key) for key in keys])


class DataLoaders(WithContextMixin):
    @cached_property
    def profile(self):
        return UserProfileLoader(context=self.context)
