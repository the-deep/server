
from django.core.cache import cache
from django.conf import settings
from rest_framework import serializers

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
        if not obj:
            return None
        key = URLCachedFileField.get_cache_key(obj.name)
        url = cache.get(key)
        if url:
            return url
        url = super().to_representation(obj)
        cache.set(key, url, settings.MAX_FILE_CACHE_AGE)
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
