import json

from django.core.cache import cache
from django.core.files.storage import (
    FileSystemStorage,
    default_storage,
    get_storage_class,
)
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.functional import cached_property
from rest_framework import serializers

from deep.caches import CacheKey, local_cache
from deep.middleware import get_s3_signed_url_ttl

StorageClass = get_storage_class()


def remove_null(d):
    if not isinstance(d, (dict, list)):
        return d

    if isinstance(d, list):
        return [v for v in (remove_null(v) for v in d) if v is not None]

    return {k: v for k, v in ((k, remove_null(v)) for k, v in d.items()) if v is not None}


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
                    data[field] = ""
        return super().to_internal_value(data)


class RecursiveSerializer(serializers.Serializer):
    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data


class URLCachedFileField(serializers.FileField):
    @classmethod
    def get_cache_key(cls, filename):
        return CacheKey.URL_CACHED_FILE_FIELD_KEY_FORMAT.format(hash(filename))

    @staticmethod
    def generate_url(name, parameters=None):
        if StorageClass == FileSystemStorage:
            return default_storage.url(str(name))
        # OR s3 storage
        return default_storage.url(str(name), parameters=parameters)

    @classmethod
    def name_to_representation(cls, name):
        """
        Caching signed url server-side
        NOTE: Using storage_class.url directly
        Assumptions:
            - Single storage is used (accessable by get_storage_class)
            - Either FileSystemStorage(local/default) or S3Boto3Storage(prod/deep.s3_storages.MediaStorage) is used.
        """
        name = str(name)

        if StorageClass == FileSystemStorage:
            return default_storage.url(name)

        # Cache for S3Boto3Storage
        if not name:
            return None
        key = URLCachedFileField.get_cache_key(name)
        url = cache.get(key)
        if url:
            return url
        url = default_storage.url(name)
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
        child=IntegerIDField(),
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


class WriteOnlyOnCreateSerializerMixin:
    """
    Allow to define fields only writable on creation
    """

    def get_fields(self, *args, **kwargs):
        fields = super().get_fields(*args, **kwargs)
        write_only_on_create_fields = getattr(self.Meta, "write_only_on_create_fields", [])
        request = self.context.get("request", None)
        if request and getattr(request, "method", None) != "POST":
            for field in write_only_on_create_fields:
                fields[field].read_only = True
        return fields


class TempClientIdMixin(serializers.ModelSerializer):
    """
    ClientId for serializer level only, storing to database is optional (if field exists).
    """

    client_id = serializers.CharField(required=False)

    @staticmethod
    def get_cache_key(instance, request):
        return CacheKey.TEMP_CLIENT_ID_KEY_FORMAT.format(
            request_hash=hash(request),
            instance_type=type(instance).__name__,
            instance_id=instance.pk,
        )

    def _get_temp_client_id(self, validated_data):
        # For now, let's not save anything. Look at history if not.
        return validated_data.pop("client_id", None)

    def create(self, validated_data):
        temp_client_id = self._get_temp_client_id(validated_data)
        instance = super().create(validated_data)
        if temp_client_id:
            instance.client_id = temp_client_id
            local_cache.set(self.get_cache_key(instance, self.context["request"]), temp_client_id, 60)
        return instance

    def update(self, instance, validated_data):
        temp_client_id = self._get_temp_client_id(validated_data)
        instance = super().update(instance, validated_data)
        if temp_client_id:
            instance.client_id = temp_client_id
            local_cache.set(self.get_cache_key(instance, self.context["request"]), temp_client_id, 60)
        return instance


class ProjectPropertySerializerMixin(serializers.Serializer):
    project_property_attribute = None

    @cached_property
    def project(self):
        project = self.context["request"].active_project
        # This is a rare case, just to make sure this is validated
        if self.instance:
            model_with_project = self.instance
            if self.project_property_attribute:
                model_with_project = getattr(self.instance, self.project_property_attribute)
            if model_with_project is None or model_with_project.project != project:
                raise serializers.ValidationError("Invalid access")
        return project

    @cached_property
    def current_user(self):
        return self.context["request"].user


class IntegerIDField(serializers.IntegerField):
    """
    This field is created to override the graphene conversion of the integerfield -> graphene.ID
    check out utils/graphene/mutation.py
    """

    pass


class StringIDField(serializers.CharField):
    """
    This field is created to override the graphene conversion of the charField -> graphene.ID
    check out utils/graphene/mutation.py
    """

    pass


class GraphqlSupportDrfSerializerJSONField(serializers.JSONField):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.encoder = self.encoder or DjangoJSONEncoder

    def to_internal_value(self, data):
        try:
            if self.binary or getattr(data, "is_json_string", False):
                if isinstance(data, bytes):
                    data = data.decode()
                return json.loads(data, cls=self.decoder)
            else:
                data = json.loads(json.dumps(data, cls=self.encoder))
        except (TypeError, ValueError):
            self.fail("invalid")
        return data
