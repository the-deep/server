from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers
from .models import Export


class ExportSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    """
    Serializer for export
    """

    class Meta:
        model = Export
        fields = ('__all__')
