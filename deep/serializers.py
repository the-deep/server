from django.core.files.storage import FileSystemStorage, get_storage_class
from django.core.cache import cache
from rest_framework import serializers

from deep.middleware import get_s3_signed_url_ttl
from .writable_nested_serializers import ( # noqa F401
    ListToDictField,
    NestedCreateMixin,
    NestedUpdateMixin,
    UniqueFieldsMixin,
)


def remove_null(d):
    if not isinstance(d, (dict, list)):
        return d

    if isinstance(d, list):
        return [v for v in (remove_null(v) for v in d) if v is not None]

    return {
        k: v
        for k, v in (
            (k, remove_null(v))
            for k, v in d.items()
        )
        if v is not None
    }


class RemoveNullFieldsMixin:
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        return remove_null(rep)

    def to_internal_value(self, data):
        # Change None char fields to blanks
        # TODO: Handle list and dict of charfields as well
        for field, field_type in self.fields.items():
            if isinstance(field_type, serializers.CharField):
                if field in data and not data.get(field):
                    data[field] = ''
        return super().to_internal_value(data)


class RecursiveSerializer(serializers.Serializer):
    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data


class URLCachedFileField(serializers.FileField):
    CACHE_KEY = 'url_cache_{}'

    @classmethod
    def get_cache_key(cls, filename):
        return cls.CACHE_KEY.format(hash(filename))

    # obj is django models.FileField
    def to_representation(self, obj):
        """
        Caching signed url server-side
        Assumptions:
            - Single storage is used (accessable by get_storage_class)
            - Either FileSystemStorage(local/default) or S3Boto3Storage(prod/deep.s3_storages.MediaStorage) is used.
        """
        # No need to cache for FileSystemStorage
        if get_storage_class() == FileSystemStorage:
            return super().to_representation(obj)

        # Cache for S3Boto3Storage
        if not obj:
            return None
        key = URLCachedFileField.get_cache_key(obj.name)
        url = cache.get(key)
        if url:
            return url
        url = super().to_representation(obj)
        cache.set(key, url, get_s3_signed_url_ttl())
        return url


# required=False List Integer Field
def IdListField():
    return serializers.ListField(
        child=serializers.IntegerField(),
        default=list,
        allow_empty=True,
    )


# required=False List String Field
def StringListField():
    return serializers.ListField(
        child=serializers.CharField(),
        default=list,
        allow_empty=True,
    )
