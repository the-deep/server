from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers

from deep.serializers import RemoveNullFieldsMixin
from .models import Export


class ExportSerializer(RemoveNullFieldsMixin,
                       DynamicFieldsMixin, serializers.ModelSerializer):
    """
    Serializer for export
    """

    class Meta:
        model = Export
        exclude = ('filters',)
