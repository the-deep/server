from promise import Promise
from django.utils.functional import cached_property
from django.conf import settings

from utils.graphene.dataloaders import DataLoaderWithContext, WithContextMixin
from deep.serializers import URLCachedFileField

from .models import (
    User,
    Profile,
)


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


class UserDisplayNameLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        display_name_qs = User.objects.filter(pk__in=keys)
        display_name_map = {}
        for user in display_name_qs:
            if user.profile.deleted_at:
                display_name_map[user.id] = settings.DELETED_USER_FIRST_NAME + ' ' + settings.DELETED_USER_LAST_NAME
            else:
                display_name_map[user.id] = Profile.get_display_name_for_user(user)
        return Promise.resolve([display_name_map.get(key) for key in keys])


class UserFirstNameLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        first_name_qs = User.objects.filter(pk__in=keys)
        first_name_map = {}
        for user in first_name_qs:
            if user.profile.deleted_at:
                first_name_map[user.id] = settings.DELETED_USER_FIRST_NAME
            else:
                first_name_map[user.id] = user.first_name
        return Promise.resolve([first_name_map.get(key) for key in keys])


class UserLastNameLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        last_name_qs = User.objects.filter(pk__in=keys)
        last_name_map = {}
        for user in last_name_qs:
            if user.profile.deleted_at:
                last_name_map[user.id] = settings.DELETED_USER_LAST_NAME
            else:
                last_name_map[user.id] = user.last_name
        return Promise.resolve([last_name_map.get(key) for key in keys])


class DataLoaders(WithContextMixin):
    @cached_property
    def display_picture(self):
        return UserDisplayPictureLoader(context=self.context)

    @cached_property
    def organization(self):
        return UserOrganizationLoader(context=self.context)

    @cached_property
    def display_name(self):
        return UserDisplayNameLoader(context=self.context)

    @cached_property
    def first_name(self):
        return UserFirstNameLoader(context=self.context)

    @cached_property
    def last_name(self):
        return UserLastNameLoader(context=self.context)
