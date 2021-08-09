from django.core.files.storage import FileSystemStorage, get_storage_class
from django.core.exceptions import FieldDoesNotExist
from django.core.cache import cache
from rest_framework import serializers

from deep.middleware import get_s3_signed_url_ttl

StorageClass = get_storage_class()


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


class RemoveNullFieldsMixin():
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

    @classmethod
    def name_to_representation(cls, name):
        """
        Caching signed url server-side
        NOTE: Using storage_class.url directly
        Assumptions:
            - Single storage is used (accessable by get_storage_class)
            - Either FileSystemStorage(local/default) or S3Boto3Storage(prod/deep.s3_storages.MediaStorage) is used.
        """
        if StorageClass == FileSystemStorage:
            return StorageClass().url(name)

        # Cache for S3Boto3Storage
        if not name:
            return None
        key = URLCachedFileField.get_cache_key(name)
        url = cache.get(key)
        if url:
            return url
        url = StorageClass().url(name)
        cache.set(key, url, get_s3_signed_url_ttl())
        return url

    # obj is django models.FileField
    def to_representation(self, obj):
        """
        Caching signed url server-side
        Assumptions:
            - Single storage is used (accessable by get_storage_class)
            - Either FileSystemStorage(local/default) or S3Boto3Storage(prod/deep.s3_storages.MediaStorage) is used.
        """
        # No need to cache for FileSystemStorage
        if StorageClass == FileSystemStorage:
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


class WriteOnlyOnCreateSerializerMixin():
    """
    Allow to define fields only writable on creation
    """
    def get_fields(self, *args, **kwargs):
        fields = super().get_fields(*args, **kwargs)
        write_only_on_create_fields = getattr(self.Meta, 'write_only_on_create_fields', [])
        request = self.context.get('request', None)
        if request and getattr(request, 'method', None) != 'POST':
            for field in write_only_on_create_fields:
                fields[field].read_only = True
        return fields


class TempClientIdMixin(serializers.ModelSerializer):
    """
    ClientId for serializer level only, storing to database is optional (if field exists).
    """
    client_id = serializers.CharField(required=False)

    def _get_temp_client_id(self, validated_data):
        try:
            self.Meta.model._meta.get_field('client_id')
            # We return None here if Model have a field `client_id`
            return None
        except FieldDoesNotExist:
            # We remove `client_id` from validated_data and return temp client_id
            # If we don't remove `client_id` from validated_data, then serializer will throw error on update/create
            return validated_data.pop('client_id', None)

    def create(self, validated_data):
        temp_client_id = self._get_temp_client_id(validated_data)
        instance = super().create(validated_data)
        if temp_client_id:
            instance.client_id = temp_client_id
        return instance

    def update(self, instance, validated_data):
        temp_client_id = self._get_temp_client_id(validated_data)
        instance = super().update(instance, validated_data)
        if temp_client_id:
            instance.client_id = temp_client_id
        return instance


class IntegerIDField(serializers.IntegerField):
    """
    This field is created to override the graphene conversion of the integerfield
    check out utils/graphene/mutation.py
    """
    pass
