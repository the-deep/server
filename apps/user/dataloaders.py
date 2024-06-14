from collections import defaultdict

from django.utils.functional import cached_property
from promise import Promise
from user.models import User

from utils.graphene.dataloaders import DataLoaderWithContext, WithContextMixin

from .models import Profile


class UserProfileLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        profile_qs = (
            Profile.objects.filter(user__in=keys)
            .select_related("display_picture")
            .only(
                "user_id",
                "organization",
                "display_picture__file",
            )
        )
        _map = {profile.user_id: profile for profile in profile_qs}
        return Promise.resolve([_map.get(key) for key in keys])


class UserLoader(DataLoaderWithContext):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def batch_load_fn(self, keys):
        users_qs = User.objects.filter(id__in=keys)
        _map = defaultdict()
        for user in users_qs:
            _map[user.id] = user
        return Promise.resolve([_map.get(key) for key in keys])


class DataLoaders(WithContextMixin):
    @cached_property
    def profile(self):
        return UserProfileLoader(context=self.context)

    @cached_property
    def users(self):
        return UserLoader(context=self.context)
