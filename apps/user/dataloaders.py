from promise import Promise
from django.utils.functional import cached_property

from deep.dataloaders import DataLoaderWithContext, WithContextMixin
from deep.serializers import URLCachedFileField

from .models import User


class UserDisplayPictureLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        display_picture_qs = User.objects.filter(pk__in=keys).values_list('id', 'profile__display_picture__file')
        # Membership map
        display_picture_map = {}
        for user_id, display_picture in display_picture_qs:
            if display_picture:
                display_picture_map[user_id] = self.context.request.build_absolute_uri(
                    URLCachedFileField.name_to_representation(display_picture)
                )
        return Promise.resolve([display_picture_map.get(key) for key in keys])


class UserOrganizationLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        organization_qs = User.objects.filter(pk__in=keys).values_list('id', 'profile__organization')
        organization_map = {
            user_id: organization for user_id, organization in organization_qs
        }
        return Promise.resolve([organization_map.get(key) for key in keys])


class DataLoaders(WithContextMixin):
    @cached_property
    def display_picture(self):
        return UserDisplayPictureLoader(context=self.context)

    @cached_property
    def organization(self):
        return UserOrganizationLoader(context=self.context)
