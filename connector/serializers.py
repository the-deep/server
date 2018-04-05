from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers

from deep.serializers import RemoveNullFieldsMixin
from lead.models import Lead


class SourceOptionSerializer(RemoveNullFieldsMixin,
                             DynamicFieldsMixin,
                             serializers.Serializer):
    key = serializers.CharField()
    field_type = serializers.CharField()
    title = serializers.CharField()


class SourceSerializer(RemoveNullFieldsMixin,
                       DynamicFieldsMixin,
                       serializers.Serializer):
    title = serializers.CharField()
    key = serializers.CharField()
    options = SourceOptionSerializer(many=True)


class SourceDataSerializer(RemoveNullFieldsMixin,
                           serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = ('title', 'source', 'source_type', 'url',
                  'website', 'text', 'published_on')
